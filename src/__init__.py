from .types import SearchResult, DownloadProgress, DownloadStatus
from .client import SoulseekClient
from .events import Event
from .exceptions import (
    SoulseekError,
    AuthenticationError,
    ConnectionClosedError,
    ProtocolError,
    DownloadError,
)

__all__ = [
    "SoulseekClient",
    "SearchResult",
    "DownloadProgress",
    "DownloadStatus",
    "Event",
    "SoulseekError",
    "AuthenticationError",
    "ConnectionClosedError",
    "ProtocolError",
    "DownloadError",
]

__version__ = "0.1.0"