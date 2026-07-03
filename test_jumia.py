import asyncio
from src.scraper.jumia import search_jumia

async def main():
    res = await search_jumia("iphone 11")
    print(res)

asyncio.run(main())
