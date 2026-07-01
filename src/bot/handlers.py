import time
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.services.search import perform_search
from src.database.json_db import JsonDatabase

logger = logging.getLogger(__name__)
db = JsonDatabase()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "\U0001f44b *Welcome to the Jumia Price Sniper Bot!*\n\n"
        "I am an advanced AI assistant engineered to help you find the absolute best deals on Jumia Nigeria. "
        "I will scan multiple listings, filter out suspicious or irrelevant items, and identify the most trusted vendors for you.\n\n"
        "Type `/help` to see how to use my features."
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "\U0001f916 *How to use the Jumia Price Sniper Bot:*\n\n"
        "\U0001f538 `/start` - Displays the welcome message and initializes the bot.\n"
        "\U0001f538 `/help` - Shows this list of instructions.\n"
        "\U0001f538 `/search <product name>` - Runs a comprehensive market analysis. "
        "Example: `/search iPhone 15 Pro`\n\n"
        "_Tip: After searching, you can click the \"Track Price Drops\" button to be notified of future discounts!_"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "\u26a0\ufe0f Please provide a product to search for. Example: `/search iPhone 15`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    raw_query = " ".join(context.args)
    start_time = time.perf_counter()

    loading_msg = await update.message.reply_text(
        f"\u2699\ufe0f Optimizing search query: '{raw_query}'... \u23f3"
    )

    gemini_start = time.perf_counter()
    try:
        result = await perform_search(raw_query)
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        await loading_msg.edit_text(
            "\u274c *An unexpected error occurred.* Please try again later.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    gemini_time = time.perf_counter() - gemini_start

    if "error" in result:
        await loading_msg.edit_text(
            f"\u274c *Failed to snipe product:*\n{result['error']}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    clean_name = result["best_match_name"].replace("[", "(").replace("]", ")")
    total_time = time.perf_counter() - start_time

    context.user_data.setdefault("searches", {})[raw_query] = {
        "product": result["best_match_name"],
        "price": int(result["best_price"].replace(",", "")),
    }

    success_text = (
        f"\U0001f4ca *Market Analysis for {raw_query}*\n"
        f"\u23f1\ufe0f *Speed:* AI {gemini_time:.2f}s | Total {total_time:.2f}s\n"
        f"Found {result['valid_results_count']} authentic listings.\n"
        f"\U0001f4c9 Price Range: \u20a6{result['range_min']} - \u20a6{result['range_max']}\n\n"
        f"\U0001f525 *Best Trusted Deal:*\n"
        f"\U0001f4f1 {clean_name}\n"
        f"\U0001f4b0 \u20a6{result['best_price']}\n"
        f"\U0001f517 [View on Jumia]({result['best_link']})"
    )

    keyboard = [
        [InlineKeyboardButton("\U0001f514 Track Price Drops", callback_data=f"track_{raw_query[:20]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await loading_msg.edit_text(
        success_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(update.effective_chat.id)

    prefix = "track_"
    if not query.data.startswith(prefix):
        return
    raw_query_key = query.data[len(prefix):]

    searches = context.user_data.get("searches", {})
    matched_key = next((k for k in searches if k.startswith(raw_query_key)), None)
    if not matched_key:
        await query.answer("Search data expired. Please search again.", show_alert=True)
        return

    entry = searches[matched_key]
    db.add_tracked_product(chat_id, entry["product"], entry["price"])

    await query.answer(
        f"\u2705 Tracking '{entry['product']}' at \u20a6{entry['price']:,}!",
        show_alert=True,
    )

    await query.edit_message_reply_markup(reply_markup=None)
