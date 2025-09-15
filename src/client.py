"""
High-level SoulseekClient orchestrating connection, auth, search, and downloads.
"""
from __future__ import annotations
import asyncio
import contextlib
from typing import Callable, Dict, Awaitable, Optional, List, Any

from .constants import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    MSG_LOGIN_OK,
    MSG_LOGIN_ERROR,
    MSG_SEARCH_RESULT,
    PING_INTERVAL,
)
from .connection import ServerConnection
from .auth import AuthManager
from .search import SearchManager
from .download import DownloadManager
from .events import EventEmitter, Event
from .protocol import pack_message
from .exceptions import SoulseekError, ConnectionClosedError, AuthenticationError
from .types import SearchResult, DownloadHandle


class SoulseekClient:
    def __init__(
        self,
        server_host: str = DEFAULT_SERVER_HOST,
        server_port: int = DEFAULT_SERVER_PORT,
        auto_reconnect: bool = True,
        simulate: bool = False,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.auto_reconnect = auto_reconnect
        self.simulate = simulate  # If True, generate fake search results.
        self._conn: ServerConnection | None = None
        self._message_waiters: List[tuple[Callable[[dict], bool], asyncio.Future]] = []
        self._listeners: Dict[int, List[Callable]] = {}
        self._ping_task: asyncio.Task | None = None
        self.events = EventEmitter()
        self._auth_mgr = AuthManager(self._send, self._wait_for_message)
        self.search = SearchManager(self._send, self._register_listener, self._unregister_listener)
        self.downloads = DownloadManager(self.events, self._send)
        self._connected = asyncio.Event()
        self._stop_flag = False
        self._reconnect_task: asyncio.Task | None = None

    # Public API ----------------------------------------------------------------

    def on(self, event: str, callback):
        self.events.on(event, callback)

    async def connect(self):
        if self.simulate:
            # Simulation mode does not open real network connection.
            self._connected.set()
            await self.events.emit(Event.CONNECTED)
            return

        async def on_message(msg):
            await self._dispatch_message(msg)

        async def on_disconnect(exc):
            if exc:
                await self.events.emit(Event.DISCONNECTED, exc)
            else:
                await self.events.emit(Event.DISCONNECTED, None)
            self._connected.clear()
            if self.auto_reconnect and not self._stop_flag:
                if not self._reconnect_task or self._reconnect_task.done():
                    self._reconnect_task = asyncio.create_task(self._reconnect())

        self._conn = ServerConnection(
            self.server_host, self.server_port, on_message, on_disconnect
        )
        await self._conn.connect()
        self._connected.set()
        await self.events.emit(Event.CONNECTED)
        if not self._ping_task:
            self._ping_task = asyncio.create_task(self._ping_loop())

    async def authenticate(self, username: str, password: str):
        if self.simulate:
            # Accept everything in simulate mode
            await asyncio.sleep(0.2)
            await self.events.emit(Event.AUTH_SUCCEEDED, username)
            return
        try:
            await self._auth_mgr.authenticate(username, password)
            await self.events.emit(Event.AUTH_SUCCEEDED, username)
        except AuthenticationError as e:
            await self.events.emit(Event.AUTH_FAILED, str(e))
            raise

    async def search_files(self, query: str, timeout: float = 30.0):
        if self.simulate:
            async def fake_results():
                # Generate some fake results
                from .types import SearchResult, SearchResultFile
                users = ["demo_user1", "demo_user2"]
                for u in users:
                    await asyncio.sleep(0.5)
                    sr = SearchResult(
                        query=query,
                        user=u,
                        folder="Music/Albums/FakeAlbum",
                        files=[
                            SearchResultFile(filename="track1.mp3", size=3_000_000),
                            SearchResultFile(filename="track2.mp3", size=3_500_000),
                        ],
                        user_host="127.0.0.1",
                        user_port=12345,
                    )
                    await self.events.emit(Event.SEARCH_RESULT, sr)
                    yield sr
            return fake_results()
        return self.search.search(query, timeout=timeout)

    async def download_file(
        self,
        user: str,
        remote_path: str,
        host: str,
        port: int,
        destination: str,
    ) -> DownloadHandle:
        return await self.downloads.download_file(
            user=user, remote_path=remote_path, host=host, port=port, destination=destination
        )

    async def download_folder(
        self,
        user: str,
        folder_path: str,
        host: str,
        port: int,
        search_results,
        destination_dir: str,
    ):
        return await self.downloads.download_folder(
            user, folder_path, host, port, search_results, destination_dir
        )

    async def close(self):
        self._stop_flag = True
        if self._ping_task:
            self._ping_task.cancel()
            with contextlib.suppress(Exception):
                await self._ping_task
        if self._conn:
            await self._conn.close()

    # Internal helpers ----------------------------------------------------------

    async def _reconnect(self):
        await asyncio.sleep(3)
        if self._stop_flag:
            return
        try:
            await self.connect()
        except Exception as e:
            await self.events.emit(Event.LOG, f"Reconnect failed: {e}")
            if self.auto_reconnect:
                asyncio.create_task(self._reconnect())

    async def _ping_loop(self):
        while True:
            await asyncio.sleep(PING_INTERVAL)
            if not self._connected.is_set():
                continue
            # TODO: Implement actual ping message (placeholder no-op)
            # self._send(pack_message(MSG_SERVER_PING, b""))
            pass

    async def _send(self, data: bytes):
        if self.simulate:
            return
        if not self._conn:
            raise ConnectionClosedError("Not connected.")
        await self._conn.send(data)

    async def _dispatch_message(self, msg: dict):
        # Notify waiters first
        for pred, fut in list(self._message_waiters):
            if not fut.done() and pred(msg):
                fut.set_result(msg)
                self._message_waiters.remove((pred, fut))

        # Listener dispatch by code
        listeners = list(self._listeners.get(msg["code"], []))
        for cb in listeners:
            try:
                result = cb(msg)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                await self.events.emit(Event.LOG, f"Listener error: {e}")

        # Specific message types -> high-level events
        if msg["code"] == MSG_SEARCH_RESULT:
            # Decoding handled by dedicated search listeners.
            pass
        elif msg["code"] in (MSG_LOGIN_OK, MSG_LOGIN_ERROR):
            # Auth manager handles awaiting.
            pass

    def _register_listener(self, code: int, callback):
        self._listeners.setdefault(code, []).append(callback)

    def _unregister_listener(self, code: int, callback):
        if code in self._listeners:
            self._listeners[code] = [
                c for c in self._listeners[code] if c is not callback
            ]

    async def _wait_for_message(
        self, predicate, timeout: float = 10.0
    ):
        fut = asyncio.get_event_loop().create_future()
        self._message_waiters.append((predicate, fut))
        try:
            return await asyncio.wait_for(fut, timeout)
        finally:
            if not fut.done():
                fut.cancel()
            self._message_waiters = [
                (p, f) for (p, f) in self._message_waiters if f is not fut
            ]