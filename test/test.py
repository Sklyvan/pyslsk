import json
from src import SoulseekClient

with open('credentials.json', 'r') as f:
    creds = json.load(f)
    USERNAME = creds['username']
    PASSWORD = creds['password']

async def main():
    client = SoulseekClient()

    await client.connect()
    await client.authenticate(USERNAME, PASSWORD)

    async for result in await client.search_files("Radical Redemption", timeout=10):
        print("Got result from", result.user, "files:", len(result.files))

    await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
