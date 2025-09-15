from __future__ import annotations
import asyncio
import time
import uuid
from typing import Dict, Callable, Awaitable, Optional

from .types import DownloadHandle, DownloadProgress, DownloadStatus
from .exceptions import DownloadError
from .protocol import build_download_request


class DownloadManager:
    def __init__(self, event_emitter, send_server):
        self._event_emitter = event_emitter
        self._send_server = send_server  # For requesting file metadata from server if needed later.
        self._active: Dict[str, DownloadHandle] = {}
        self._lock = asyncio.Lock()

    def list_downloads(self):
        return list(self._active.values())

    async def download_file(
        self,
        user: str,
        remote_path: str,
        host: str,
        port: int,
        destination: str,
        request_via_server: bool = False,
    ) -> DownloadHandle:
        """
        Download a single file from a peer.

        This version opens a direct TCP connection and streams bytes to disk.
        Real Soulseek requires a handshake / authorization sequence (TODO).
        """
        handle = DownloadHandle(
            id=str(uuid.uuid4()),
            user=user,
            remote_path=remote_path,
            destination=destination,
        )
        async with self._lock:
            self._active[handle.id] = handle

        await self._event_emitter.emit("download_started", handle)

        # Placeholder handshake / request:
        # In a real implementation we would first connect to peer, then send a properly
        # formatted request. Here we just send the placeholder request and read raw data.
        async def _run():
            start_time = time.time()
            handle.status = DownloadStatus.CONNECTING
            try:
                reader, writer = await asyncio.open_connection(host, port)
                try:
                    # TODO: Replace with real peer handshake.
                    request = build_download_request(user, remote_path)
                    writer.write(request)
                    await writer.drain()

                    # TODO: Parse peer response header to determine file size.
                    # For now we assume unknown size.
                    handle.status = DownloadStatus.IN_PROGRESS
                    bytes_received = 0
                    with open(destination, "wb") as f:
                        while True:
                            chunk = await reader.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            bytes_received += len(chunk)
                            handle.bytes_received = bytes_received
                            elapsed = time.time() - start_time
                            rate = bytes_received / elapsed if elapsed > 0 else None
                            progress = DownloadProgress(
                                user=user,
                                remote_path=remote_path,
                                destination=destination,
                                bytes_received=bytes_received,
                                total_bytes=handle.total_bytes,
                                status=handle.status,
                                transfer_rate_bps=rate,
                            )
                            await self._event_emitter.emit("download_progress", progress)

                    handle.status = DownloadStatus.COMPLETED
                    progress = DownloadProgress(
                        user=user,
                        remote_path=remote_path,
                        destination=destination,
                        bytes_received=handle.bytes_received,
                        total_bytes=handle.total_bytes,
                        status=handle.status,
                    )
                    await self._event_emitter.emit("download_completed", progress)
                finally:
                    writer.close()
                    with contextlib.suppress(Exception):
                        await writer.wait_closed()
            except Exception as e:
                handle.status = DownloadStatus.FAILED
                handle.error = str(e)
                progress = DownloadProgress(
                    user=user,
                    remote_path=remote_path,
                    destination=destination,
                    bytes_received=handle.bytes_received,
                    total_bytes=handle.total_bytes,
                    status=handle.status,
                    error=str(e),
                )
                await self._event_emitter.emit("download_failed", progress)
                raise DownloadError(f"Failed to download {remote_path}: {e}") from e

        handle._future = asyncio.create_task(_run())
        return handle

    async def download_folder(
        self,
        user: str,
        folder_path: str,
        host: str,
        port: int,
        results,
        destination_dir: str,
    ):
        """
        Download all files that belong to folder_path from supplied search results iterable.

        results: Iterable[SearchResult] (or list).
        """
        tasks = []
        for r in results:
            if r.user != user:
                continue
            if r.folder != folder_path:
                continue
            for f in r.files:
                remote_path = f"{r.folder}/{f.filename}".replace("//", "/")
                dest = f"{destination_dir}/{f.filename}"
                tasks.append(
                    await self.download_file(
                        user=user,
                        remote_path=remote_path,
                        host=host,
                        port=port,
                        destination=dest,
                    )
                )
        return tasks

    async def cancel(self, handle_id: str):
        async with self._lock:
            handle = self._active.get(handle_id)
        if not handle:
            return
        if handle._future and not handle._future.done():
            handle._future.cancel()
            handle.status = DownloadStatus.CANCELLED
            progress = DownloadProgress(
                user=handle.user,
                remote_path=handle.remote_path,
                destination=handle.destination,
                bytes_received=handle.bytes_received,
                total_bytes=handle.total_bytes,
                status=handle.status,
            )
            await self._event_emitter.emit("download_cancelled", progress)


import contextlib  # noqa
