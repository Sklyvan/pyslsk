from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Union

EventCallback = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


class Event:
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTH_SUCCEEDED = "auth_succeeded"
    AUTH_FAILED = "auth_failed"
    SEARCH_RESULT = "search_result"
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    DOWNLOAD_CANCELLED = "download_cancelled"
    LOG = "log"


class EventEmitter:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[EventCallback]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def on(self, event: str, callback: EventCallback) -> None:
        self._listeners[event].append(callback)

    def off(self, event: str, callback: EventCallback) -> None:
        if event in self._listeners:
            self._listeners[event] = [
                c for c in self._listeners[event] if c is not callback
            ]

    async def emit(self, event: str, *args, **kwargs) -> None:
        listeners = list(self._listeners.get(event, []))
        for cb in listeners:
            try:
                result = cb(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa
                # Best-effort logging; avoid dependency on logging config
                # Consider dispatching an internal error event later.
                print(f"[EventEmitter] Listener error for '{event}': {exc}")