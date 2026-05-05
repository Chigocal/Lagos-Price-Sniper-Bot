import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

def clean_price(price_str: str) -> int:
    """Extracts integer value from a Jumia price string like '₦ 4,500'."""
    # Sometimes Jumia has ranges like "₦ 4,500 - ₦ 5,000", just take the first part
    price_str = price_str.split('-')[0]
    digits = re.sub(r'[^\d]', '', price_str)
    return int(digits) if digits else 0

async def search_jumia(query: str) -> dict:
    """
    Searches Jumia Nigeria for the query, filters results, and extracts market analysis.
    """
    url = f"https://www.jumia.com.ng/catalog/?q={query}"
    
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            try:
                await page.wait_for_selector("article.prd", timeout=15000)
            except PlaywrightTimeoutError:
                await browser.close()
                return {"error": "Timeout waiting for Jumia products to load. Check your connection or search query."}
            
            product_cards = await page.query_selector_all("article.prd")
            
            if not product_cards:
                await browser.close()
                return {"error": "No products found for this search."}
            
            valid_results = []
            all_results = []
            
            exclude_keywords = [
                "case", "cover", "screen protector", "glass", "pouch", 
                "bumper", "silicone", "tpu", "strap", "band", "lens"
            ]
            
            for card in product_cards[:20]: # Check up to 20 to find 5-10 good ones
                name_element = await card.query_selector(".info .name")
                name = await name_element.inner_text() if name_element else "Unknown Name"
                
                a_tag = await card.query_selector("a.core")
                if not a_tag:
                    continue
                    
                href = await a_tag.get_attribute("href")
                link = f"https://www.jumia.com.ng{href}" if href and href.startswith("/") else (href or "")
                
                price_element = await card.query_selector(".info .prc")
                price_str = await price_element.inner_text() if price_element else "0"
                price_val = clean_price(price_str)
                
                if price_val == 0:
                    continue
                    
                # Check for Jumia Express or Official Store badges
                # Jumia uses bdg classes or img tags for badges
                card_html = await card.inner_html()
                is_trusted = "Official Store" in card_html or "Express" in card_html
                
                item_data = {
                    "name": name.strip(),
                    "price_str": price_str.strip(),
                    "price_val": price_val,
                    "link": link,
                    "is_trusted": is_trusted
                }
                
                all_results.append(item_data)
                
                name_lower = name.lower()
                if not any(keyword in name_lower for keyword in exclude_keywords):
                    valid_results.append(item_data)
                    if len(valid_results) >= 10:
                        break
                        
            await browser.close()
            
            # Fallback if filter removed everything
            if not valid_results and all_results:
                valid_results = all_results[:10]
                
            if not valid_results:
                return {"error": "Could not extract any valid product details."}
                
            # Further filtering: Remove suspiciously cheap items if we have multiple results
            # E.g., if max price is 200k, and something is 3k, it's probably a case we missed.
            if len(valid_results) > 1:
                max_price = max(item["price_val"] for item in valid_results)
                # Keep items that are at least 10% of the max price
                price_filtered = [item for item in valid_results if item["price_val"] >= (max_price * 0.1)]
                if price_filtered:
                    valid_results = price_filtered
            
            prices = [item["price_val"] for item in valid_results]
            range_min = f"{min(prices):,}"
            range_max = f"{max(prices):,}"
            
            # Prioritize best match: Trusted and Lowest price
            # Sort by trusted first (True is better), then by price (lower is better)
            best_match = sorted(valid_results, key=lambda x: (not x["is_trusted"], x["price_val"]))[0]
            
            return {
                "best_match_name": best_match["name"],
                "best_price": f"{best_match['price_val']:,}",
                "best_link": best_match["link"],
                "range_min": range_min,
                "range_max": range_max,
                "valid_results_count": len(valid_results),
                "search_url": url
            }

    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
