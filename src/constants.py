DEFAULT_SERVER_HOST = "server.slsknet.org"
DEFAULT_SERVER_PORT = 2242  # TODO: Verify this is the actual global server port

# Message codes
MSG_LOGIN = 0x01                # TODO
MSG_LOGIN_OK = 0x02             # TODO
MSG_LOGIN_ERROR = 0x03          # TODO
MSG_SEARCH_REQUEST = 0x10       # TODO
MSG_SEARCH_RESULT = 0x11        # TODO
MSG_SERVER_PING = 0x1F          # TODO
MSG_DOWNLOAD_REQUEST = 0x30     # TODO
MSG_DOWNLOAD_ERROR = 0x31       # TODO

PING_INTERVAL = 120  # seconds
RECONNECT_DELAY = 5  # seconds
