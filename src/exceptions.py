class SoulseekError(Exception):
    """Base exception for the library."""


class AuthenticationError(SoulseekError):
    """Raised when authentication fails."""


class ConnectionClosedError(SoulseekError):
    """Raised when the connection is unexpectedly closed."""


class ProtocolError(SoulseekError):
    """Raised when a protocol violation or parse error occurs."""


class DownloadError(SoulseekError):
    """Raised when a download operation fails."""


class SearchError(SoulseekError):
    """Raised when a search request fails."""
