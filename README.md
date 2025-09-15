# 🎵 PySoulseek

**Async Python client for the Soulseek P2P network** <br>
Modular, event-driven, and ready for automation or integration.

---

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Asyncio](https://img.shields.io/badge/asyncio-supported-green)
![License: GPLv3](https://img.shields.io/badge/license-GPLv3-blue)

---

## ✨ Features

- ⚡ **Async connection management** (placeholder framing protocol)
- 🔐 **Authentication structure** (login request + success/failure)
- 🔎 **Global search** (streaming async iterator of results)
- 🪁 **Event-based architecture** for:
  - Connection lifecycle
  - Authentication
  - Search results
  - Download lifecycle (start, progress, completion, failure, cancellation)
- 📥 **File & folder download scaffolding** (direct peer connection)
- 🧪 **Simulation mode** for development/testing
- 🛡️ **Type-safe dataclasses** (`SearchResult`, `DownloadProgress`, etc.)

---

## 🚫 Not Implemented

| ❌ Feature | Description |
|---|---|
| Message codes | Real Soulseek message codes & payloads |
| Peer transfer | Authorization, encryption, slot management |
| Search logic | Real encoding/decoding |
| Error handling | Protocol-aligned errors |
| Queue/upload | Queue management, upload serving, NAT/firewall |
| User features | User list, rooms, messaging, browse, privileges |
| Download resume | Partial download logic |
| Rate limiting | Concurrency control |
| Reconnection | Robust backoff strategy |

---

## 🛠️ Installation (Local Development)

```bash
# Optional: Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Local install
pip install -e .
```

---

## 📦 Package Structure

```
src/
    __init__.py
    client.py
    connection.py
    protocol.py
    auth.py
    search.py
    download.py
    events.py
    types.py
    constants.py
    exceptions.py
.gitignore
LICENSE
pyproject.toml
README.md
```

---

## 🧩 Core Concepts

### 1️⃣ Client Lifecycle

```python
from src import SoulseekClient

client = SoulseekClient()
await client.connect()
await client.authenticate("username", "password")
# perform operations...
await client.close()
```

---

### 2️⃣ Event System

Events are emitted asynchronously. Register callbacks (sync or async):

```python
from src import Event

def on_result(result):
    print("Search result:", result.user, result.folder)

client.on(Event.SEARCH_RESULT, on_result)
```

See available event names in [`src/events.py`](src/events.py).

---

### 3️⃣ Authentication

Simple request/response flow in [auth.py](src/auth.py).

---

### 4️⃣ Searching

```python
async for result in await client.search_files("ambient chill", timeout=20):
    print("Got result from", result.user, "files:", len(result.files))
```

Streaming ends after `timeout` seconds.

---

### 5️⃣ Downloading Files

```python
handle = await client.download_file(
    user="peerUser",
    remote_path="Music/SomeFolder/track1.mp3",
    host="peer.host.example",
    port=12345,
    destination="/path/to/save/track1.mp3",
)

while not handle.done():
    await asyncio.sleep(0.5)
```

**Download events:**
- `download_started`
- `download_progress` (`DownloadProgress`)
- `download_completed`
- `download_failed`

---

### 6️⃣ Downloading an Entire Folder

```python
results = []
async for r in await client.search_files("album name"):
    results.append(r)

tasks = await client.download_folder(
    user="peerUser",
    folder_path="Music/Albums/TargetAlbum",
    host="peer.host",
    port=12345,
    search_results=results,
    destination_dir="/downloads/TargetAlbum"
)
```

---

### 7️⃣ Simulation Mode

Set `simulate=True` when creating the client:

```python
from src import SoulseekClient
client = SoulseekClient(simulate=True)
```

- Skips network connection
- Fakes authentication
- Generates artificial search results
- Goes through the same event flow

---

## 🛠️ Extending the Protocol Layer

All message building/parsing lives in [protocol.py](src/protocol.py).
Replace placeholders with real Soulseek protocol logic:

- `build_login`
- `build_search`
- `build_download_request`
- `decode_search_result`

Add new functions for user info, browse, queue control, etc.

---

## 🔒 Thread Safety / Concurrency

- Designed for asyncio event loop; **not thread-safe**
- Use `asyncio.Lock` for shared structures

---

## ⚠️ Error Handling

Custom exceptions in [exceptions.py](src/exceptions.py).

| Exception | Description |
|---|---|
| `SoulseekError` | Base |
| `AuthenticationError` | Auth failures |
| `ConnectionClosedError` | Connection issues |
| `ProtocolError` | Protocol violations |
| `DownloadError` | Download failures |
| `SearchError` | Search failures |

---

## 📄 License

If you incorporate code from existing GPLv3 Soulseek clients (e.g. Nicotine+), this project must remain GPLv3 (or compatible).  
Currently, this scaffold is original and can be adapted; GPLv3 ensures compatibility.

---

## ⚠️ Disclaimer

This library does **not** guarantee compliance with the Soulseek network or protocol stability.  
Use at your own risk. Ensure adherence to network etiquette and legal considerations when transferring files.

---

## 🚀 Example

```python
import asyncio
from src import SoulseekClient

async def run():
    client = SoulseekClient()
    await client.connect()
    await client.authenticate("user", "pass")
    async for r in await client.search_files("jazz fusion"):
        print(r.user, r.folder, [f.filename for f in r.files])
    await client.close()

asyncio.run(run())
```

---

## 🤝 Contributing

Enhance with real protocol details and expand features!  
Contributions, forks, and adaptation are encouraged under GPLv3.

---
