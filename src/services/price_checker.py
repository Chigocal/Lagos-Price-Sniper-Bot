import logging

from telegram.ext import CallbackContext
from telegram.constants import ParseMode

from src.database.json_db import JsonDatabase
from src.scraper.jumia import search_jumia
from src.services.query_cleaner import standardize_search_query
import asyncio

logger = logging.getLogger(__name__)
db = JsonDatabase()


async def check_prices(context: CallbackContext):
    all_tracked = db.get_all_tracked_products()
    if not all_tracked:
        return

    for chat_id, products in all_tracked.items():
        for entry in list(products):
            product = entry["product"]
            alert_price = entry["alert_price"]

            cleaned = await asyncio.to_thread(standardize_search_query, product)
            result = await search_jumia(cleaned)
            if "error" in result:
                # If an item is out of stock or unsearchable, it will timeout. Log it as info instead of a scary warning.
                logger.info("Price check skipped for '%s': %s", product, result["error"])
                continue

            current_price = int(result["best_price"].replace(",", ""))

            if current_price < alert_price:
                msg = (
                    f"\U0001f514 *Price Drop Alert!*\n\n"
                    f"\U0001f4f1 *{result['best_match_name']}*\n"
                    f"\U0001f4c9 Was: \u20a6{alert_price:,}\n"
                    f"\U0001f4c8 Now: \u20a6{current_price:,} (\u2193 {alert_price - current_price:,})\n"
                    f"\U0001f517 [View on Jumia]({result['best_link']})"
                )
                try:
                    await context.bot.send_message(
                        chat_id=int(chat_id),
                        text=msg,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                    logger.info("Alert sent to %s for %s: %s", chat_id, product, current_price)
                except Exception as e:
                    logger.error("Failed to send alert to %s: %s", chat_id, e)
                    continue

                db.add_tracked_product(chat_id, product, current_price)
