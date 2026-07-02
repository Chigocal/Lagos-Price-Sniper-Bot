import logging
import asyncio

from src.scraper.jumia import search_jumia
from src.scraper.client import browser_client
from src.services.query_cleaner import standardize_search_query

logger = logging.getLogger(__name__)


async def perform_search(raw_query: str) -> dict:
    cleaned_query = await asyncio.to_thread(standardize_search_query, raw_query)
    logger.info(f"Raw: {raw_query} | AI Cleaned: {cleaned_query}")

    browser = await browser_client.get_browser()
    result = await search_jumia(cleaned_query, browser)
    if "error" not in result:
        result["cleaned_query"] = cleaned_query
    return result
