import asyncio
import re

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async

EXCLUDE_KEYWORDS = [
    "case", "cover", "screen protector", "glass", "pouch",
    "bumper", "silicone", "tpu", "strap", "band", "lens",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def clean_price(price_str: str) -> int:
    price_str = price_str.split("-")[0]
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else 0


async def extract_card_data(card) -> dict | None:
    name_element = await card.query_selector(".info .name")
    if not name_element:
        return None
    name = await name_element.inner_text()

    a_tag = await card.query_selector("a.core")
    if not a_tag:
        return None

    href = await a_tag.get_attribute("href")
    if not href:
        return None
    link = f"https://www.jumia.com.ng{href}" if href.startswith("/") else href

    price_element = await card.query_selector(".info .prc")
    if not price_element:
        return None
    price_str = await price_element.inner_text()
    price_val = clean_price(price_str)
    if price_val == 0:
        return None

    trusted = False
    badge = await card.query_selector(".bdg")
    if badge:
        badge_text = await badge.inner_text()
        trusted = "official store" in badge_text.lower() or "express" in badge_text.lower()
    if not trusted:
        img_badge = await card.query_selector("img[alt*='Official'], img[alt*='Express']")
        if img_badge:
            trusted = True

    return {
        "name": name.strip(),
        "price_str": price_str.strip(),
        "price_val": price_val,
        "link": link,
        "is_trusted": trusted,
    }


async def search_jumia(query: str, browser) -> dict:
    url = f"https://www.jumia.com.ng/catalog/?q={query}"
    context = await browser.new_context(
        user_agent=USER_AGENT,
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
    )
    try:
        page: Page = await context.new_page()
        await stealth_async(page)
        
        # Hide webdriver flag to bypass basic bot protection
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        async def block_aggressively(route, request):
            if request.resource_type in ["image", "stylesheet", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_aggressively)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("article.prd", timeout=15000)
        except PlaywrightTimeoutError:
            screenshot_bytes = await page.screenshot(full_page=True)
            return {
                "error": "Timeout waiting for Jumia products to load.",
                "screenshot": screenshot_bytes
            }
        except Exception:
            return {"error": "Failed to load Jumia search page. Check your connection."}

        product_cards = await page.query_selector_all("article.prd")
        if not product_cards:
            return {"error": "No products found for this search."}

        cards_to_process = product_cards[:20]
        card_data = await asyncio.gather(*[extract_card_data(c) for c in cards_to_process])

        all_results = [r for r in card_data if r is not None]
        if not all_results:
            return {"error": "Could not extract any valid product details."}

        valid_results = [
            r for r in all_results
            if not any(kw in r["name"].lower() for kw in EXCLUDE_KEYWORDS)
        ]
        if not valid_results:
            valid_results = all_results[:10]

        if len(valid_results) > 1:
            max_price = max(item["price_val"] for item in valid_results)
            price_filtered = [item for item in valid_results if item["price_val"] >= (max_price * 0.1)]
            if price_filtered:
                valid_results = price_filtered

        prices = [item["price_val"] for item in valid_results]
        best_match = sorted(valid_results, key=lambda x: (not x["is_trusted"], x["price_val"]))[0]

        return {
            "best_match_name": best_match["name"],
            "best_price": f"{best_match['price_val']:,}",
            "best_link": best_match["link"],
            "range_min": f"{min(prices):,}",
            "range_max": f"{max(prices):,}",
            "valid_results_count": len(valid_results),
            "search_url": url,
        }
    except Exception:
        return {"error": "An unexpected error occurred while scraping Jumia."}
    finally:
        await context.close()
