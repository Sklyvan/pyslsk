from __future__ import annotations
import asyncio
from typing import Optional

from .constants import MSG_LOGIN_OK, MSG_LOGIN_ERROR
from .protocol import build_login
from .exceptions import AuthenticationError, ProtocolError


class AuthManager:
    def __init__(self, send_func, wait_for_message):
        self._send = send_func
        self._wait_for_message = wait_for_message
        self._lock = asyncio.Lock()
        self.username: Optional[str] = None

    async def authenticate(self, username: str, password: str, timeout: float = 10.0):
        async with self._lock:
            self.username = username
            await self._send(build_login(username, password))
            msg = await self._wait_for_message(
                lambda m: m["code"] in (MSG_LOGIN_OK, MSG_LOGIN_ERROR),
                timeout=timeout,
            )
            if msg["code"] == MSG_LOGIN_OK:
                return True
            elif msg["code"] == MSG_LOGIN_ERROR:
                raise AuthenticationError("Login rejected by server.")
            else:
                raise ProtocolError("Unexpected message during authentication.")
