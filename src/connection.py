from __future__ import annotations
from .exceptions import ConnectionClosedError, ProtocolError
from typing import Optional, Callable, Awaitable
from .protocol import iter_frames, parse_message
import asyncio


class ServerConnection:
    def __init__(
        self,
        host: str,
        port: int,
        on_message: Callable[[dict], Awaitable[None]],
        on_disconnect: Callable[[Exception | None], Awaitable[None]],
    ):
        self.host = host
        self.port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._task: asyncio.Task | None = None
        self._recv_buffer = bytearray()
        self._on_message = on_message
        self._on_disconnect = on_disconnect
        self._closed = asyncio.Event()

    async def connect(self, timeout: float = 10.0):
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=timeout
        )
        self._task = asyncio.create_task(self._recv_loop())

    async def _recv_loop(self):
        exc: Exception | None = None
        try:
            while True:
                chunk = await self._reader.read(4096)
                if not chunk:
                    raise ConnectionClosedError("Server closed the connection.")
                self._recv_buffer.extend(chunk)
                for frame in iter_frames(self._recv_buffer):
                    msg = parse_message(frame)
                    await self._on_message(msg)
        except Exception as e:
            exc = e
        finally:
            await self._on_disconnect(exc)
            self._closed.set()

    async def send(self, data: bytes):
        if not self._writer:
            raise ConnectionClosedError("Not connected")
        self._writer.write(data)
        await self._writer.drain()

    async def close(self):
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        if self._task:
            self._task.cancel()
            with contextlib.suppress(Exception):
                await self._task
        await self._on_disconnect(None)
        self._closed.set()

    async def wait_closed(self):
        await self._closed.wait()


import contextlib  # noqa: E402 (import after class acceptable for clarity)
