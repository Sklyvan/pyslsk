from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


@dataclass
class SearchResultFile:
    filename: str
    size: int
    bitrate: Optional[int] = None
    length_seconds: Optional[int] = None
    # Additional meta fields can be added as needed.


@dataclass
class SearchResult:
    query: str
    user: str
    folder: str
    files: List[SearchResultFile]
    user_host: Optional[str] = None  # Resolved/received host for the peer
    user_port: Optional[int] = None  # Resolved/received port for the peer
    raw_payload: bytes | None = None  # For debugging/protocol development


class DownloadStatus(Enum):
    QUEUED = "queued"
    CONNECTING = "connecting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    user: str
    remote_path: str
    destination: str
    bytes_received: int
    total_bytes: Optional[int]
    status: DownloadStatus
    error: Optional[str] = None
    transfer_rate_bps: Optional[float] = None
    # Add timestamp or ETA if desired.


@dataclass
class DownloadHandle:
    id: str
    user: str
    remote_path: str
    destination: str
    status: DownloadStatus = DownloadStatus.QUEUED
    total_bytes: Optional[int] = None
    bytes_received: int = 0
    error: Optional[str] = None
    _future: Optional["asyncio.Future"] = field(default=None, repr=False, compare=False)

    def done(self) -> bool:
        return self.status in {
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        }
