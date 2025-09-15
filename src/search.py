from __future__ import annotations
import asyncio
from typing import AsyncIterator, Callable

from .constants import MSG_SEARCH_RESULT
from .protocol import build_search, decode_search_result
from .types import SearchResult, SearchResultFile
from .exceptions import SearchError


class SearchManager:
    def __init__(self, send_func, register_listener, unregister_listener):
        self._send = send_func
        self._register = register_listener
        self._unregister = unregister_listener

    async def search(self, query: str, timeout: float = 30.0) -> AsyncIterator[SearchResult]:
        """
        Perform a global search and yield results as they arrive for the given timeout.
        """
        queue: asyncio.Queue[SearchResult | None] = asyncio.Queue()

        async def listener(msg):
            try:
                decoded = decode_search_result(msg["payload"])
                if decoded["query"].lower() != query.lower():
                    return
                files = [
                    SearchResultFile(filename=f["filename"], size=f["size"])
                    for f in decoded["files"]
                ]
                result = SearchResult(
                    query=decoded["query"],
                    user=decoded["user"],
                    folder=decoded["folder"],
                    files=files,
                    raw_payload=msg["payload"],
                )
                await queue.put(result)
            except Exception as e:
                # Best effort: ignore malformed result
                print(f"[SearchManager] Failed to decode search result: {e}")

        self._register(MSG_SEARCH_RESULT, listener)
        try:
            await self._send(build_search(query))
            # Yield until timeout
            stop = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = stop - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=remaining)
                except asyncio.TimeoutError:
                    break
                if item is None:
                    break
                yield item
        finally:
            self._unregister(MSG_SEARCH_RESULT, listener)