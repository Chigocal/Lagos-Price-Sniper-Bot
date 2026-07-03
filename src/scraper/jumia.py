from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import re

EXCLUDE_KEYWORDS = [
    "case", "cover", "screen protector", "glass", "pouch",
    "bumper", "silicone", "tpu", "strap", "band", "lens",
]

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36'
}

def clean_price(price_str: str) -> int:
    price_str = price_str.split("-")[0]
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else 0

async def search_jumia(query: str) -> dict:
    url = f"https://www.jumia.com.ng/catalog/?q={query}"
    
    try:
        # We use curl_cffi to spoof the TLS fingerprint of Chrome
        # We purposely do NOT send the cookies from the user's browser, 
        # because Cloudflare ties those cookies to the user's IP. Sending them from the server causes a 403.
        async with AsyncSession(impersonate="chrome120") as client:
            response = await client.get(url, headers=HEADERS, timeout=30.0)
            
            if response.status_code != 200:
                return {"error": f"Failed to load Jumia search page. Status code: {response.status_code}"}
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            product_cards = soup.select("article.prd")
            if not product_cards:
                return {"error": "No products found for this search. (Or blocked by Cloudflare Captcha)"}

            valid_results = []
            
            for card in product_cards[:20]:
                name_element = card.select_one(".info .name")
                if not name_element:
                    continue
                name = name_element.get_text(strip=True)

                a_tag = card.select_one("a.core")
                href_attr = a_tag.get("href") if a_tag else None
                if not href_attr:
                    continue
                
                href = href_attr[0] if isinstance(href_attr, list) else href_attr
                link = f"https://www.jumia.com.ng{href}" if href.startswith("/") else href

                price_element = card.select_one(".info .prc")
                if not price_element:
                    continue
                price_str = price_element.get_text(strip=True)
                price_val = clean_price(price_str)
                if price_val == 0:
                    continue

                trusted = False
                badge = card.select_one(".bdg")
                if badge:
                    badge_text = badge.get_text(strip=True).lower()
                    trusted = "official store" in badge_text or "express" in badge_text
                
                if not trusted:
                    img_badges = card.select("img")
                    for img in img_badges:
                        alt_attr = img.get("alt")
                        if not alt_attr:
                            continue
                            
                        alt = alt_attr[0] if isinstance(alt_attr, list) else alt_attr
                        alt_lower = alt.lower()
                        
                        if "official" in alt_lower or "express" in alt_lower:
                            trusted = True
                            break

                valid_results.append({
                    "name": name,
                    "price_str": price_str,
                    "price_val": price_val,
                    "link": link,
                    "is_trusted": trusted,
                })

            if not valid_results:
                return {"error": "Could not extract any valid product details."}

            filtered = [
                r for r in valid_results
                if not any(kw in r["name"].lower() for kw in EXCLUDE_KEYWORDS)
            ]
            if not filtered:
                filtered = valid_results[:10]

            if len(filtered) > 1:
                max_price = max(item["price_val"] for item in filtered)
                price_filtered = [item for item in filtered if item["price_val"] >= (max_price * 0.1)]
                if price_filtered:
                    filtered = price_filtered

            prices = [item["price_val"] for item in filtered]
            best_match = sorted(filtered, key=lambda x: (not x["is_trusted"], x["price_val"]))[0]

            return {
                "best_match_name": best_match["name"],
                "best_price": f"{best_match['price_val']:,}",
                "best_link": best_match["link"],
                "range_min": f"{min(prices):,}",
                "range_max": f"{max(prices):,}",
                "valid_results_count": len(filtered),
                "search_url": url,
            }

    except Exception as e:
        return {"error": f"An unexpected error occurred while scraping Jumia: {e}"}
