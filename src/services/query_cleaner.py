import logging
import requests

from src.config import settings
from src.scraper.cache import search_cache

logger = logging.getLogger(__name__)


def standardize_search_query(raw_query: str) -> str:
    cached = search_cache.get(raw_query)
    if cached:
        logger.info(f"Cache hit for query: {raw_query} -> {cached}")
        return cached

    if not settings.gemini_api_key:
        return raw_query

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}"

    prompt = (
        "You are a search query optimizer for an e-commerce bot. "
        "The user will provide a messy, misspelled gadget name. "
        "Your ONLY job is to return the perfectly spelled, standard brand and model name. "
        "Fix typos (e.g., 'reddmi' -> 'Redmi', 'ihpone' -> 'iPhone') and standard specs (e.g., '256gig' -> '256GB'). "
        "DO NOT include any conversational text, markdown formatting, or explanations. "
        "Return ONLY the corrected string. If it is already correct, return it as is.\n\n"
        f"Query: {raw_query}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0},
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        response.raise_for_status()
        data = response.json()
        clean_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        clean_text = clean_text.strip("'\" \n")

        search_cache.set(raw_query, clean_text)
        return clean_text
    except Exception as e:
        logger.error(f"Gemini AI query correction failed: {e}")
        return raw_query
