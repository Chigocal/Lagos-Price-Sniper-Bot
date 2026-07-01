import os
import time
import json
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from scraper import search_jumia
from extractor import standardize_search_query

# Load environment variables from .env file
load_dotenv()

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    welcome_message = (
        "👋 *Welcome to the Jumia Price Sniper Bot!*\n\n"
        "I am an advanced AI assistant engineered to help you find the absolute best deals on Jumia Nigeria. "
        "I will scan multiple listings, filter out suspicious or irrelevant items, and identify the most trusted vendors for you.\n\n"
        "Type `/help` to see how to use my features."
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command."""
    help_message = (
        "🤖 *How to use the Jumia Price Sniper Bot:*\n\n"
        "🔸 `/start` - Displays the welcome message and initializes the bot.\n"
        "🔸 `/help` - Shows this list of instructions.\n"
        "🔸 `/search <product name>` - Runs a comprehensive market analysis. "
        "Example: `/search iPhone 15 Pro`\n\n"
        "_Tip: After searching, you can click the \"Track Price Drops\" button to be notified of future discounts!_"
    )
    await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /search command."""
    # Check if user provided a product name
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a product to search for. Example: `/search iPhone 15`", 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Join the arguments to form the search query
    raw_query = " ".join(context.args)
    
    # Start the performance timer
    start_time = time.perf_counter()
    
    # Send the initial loading message
    loading_message = await update.message.reply_text(
        f"⚙️ Optimizing search query: '{raw_query}'... ⏳"
    )
    
    # Run the Gemini AI query standardizer in a background thread
    import asyncio
    gemini_start = time.perf_counter()
    cleaned_query = await asyncio.to_thread(standardize_search_query, raw_query)
    gemini_time = time.perf_counter() - gemini_start
    
    # Log the AI correction for monitoring
    logger.info(f"Raw: {raw_query} | AI Cleaned: {cleaned_query}")
    
    await loading_message.edit_text(
        f"🔍 Infiltrating Jumia for '{cleaned_query}'...\nAnalyzing prices and filtering trusted vendors... ⏳"
    )
    
    # Run the scraper using the CLEANED query
    scraper_start = time.perf_counter()
    try:
        result = await search_jumia(cleaned_query)
        scraper_time = time.perf_counter() - scraper_start
        
        if "error" in result:
            # Edit the loading message with the error
            await loading_message.edit_text(
                f"❌ *Failed to snipe product:*\n{result['error']}", 
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Escape brackets in the name to prevent markdown link breaking
            clean_name = result['best_match_name'].replace('[', '(').replace(']', ')')
            
            # Calculate elapsed time
            total_time = time.perf_counter() - start_time
            
            # Format the success message
            success_text = (
                f"📊 *Market Analysis for {cleaned_query}*\n"
                f"⏱️ *Speed:* AI {gemini_time:.2f}s | Scraper {scraper_time:.2f}s | Total {total_time:.2f}s\n"
                f"Found {result['valid_results_count']} authentic listings.\n"
                f"📉 Price Range: ₦{result['range_min']} - ₦{result['range_max']}\n\n"
                f"🔥 *Best Trusted Deal:*\n"
                f"📱 {clean_name}\n"
                f"💰 ₦{result['best_price']}\n"
                f"🔗 [View on Jumia]({result['best_link']})"
            )
            
            # Create Inline Keyboard for tracking
            # We slice the query to ensure callback_data stays within Telegram's 64 byte limit
            clean_price = int(result['best_price'].replace(",", ""))
            track_data = f"track|{clean_price}|{cleaned_query[:40]}"
            keyboard = [
                [InlineKeyboardButton("🔔 Track Price Drops", callback_data=track_data)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Edit the message with the final results and attach the button
            await loading_message.edit_text(
                success_text, 
                parse_mode=ParseMode.MARKDOWN, 
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Error during search: {e}")
        await loading_message.edit_text("❌ An unexpected error occurred while communicating with the scraper.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline keyboard button clicks."""
    query = update.callback_query
    
    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()
    
    if query.data.startswith("track|"):
        parts = query.data.split("|")
        alert_price = int(parts[1])
        product_name = parts[2]
        user_id = str(query.from_user.id)
        
        db = load_db()
        if user_id not in db:
            db[user_id] = []
            
        # Check if already tracking
        already_tracking = any(item.get("product") == product_name for item in db[user_id])
        
        if not already_tracking:
            db[user_id].append({"product": product_name, "alert_price": alert_price})
            save_db(db)
            await query.message.reply_text(f"✅ You are now tracking price drops for: {product_name}. I will DM you if the price goes down!")
        else:
            await query.message.reply_text(f"ℹ️ You are already tracking {product_name}.")

async def check_prices_background(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check for price drops."""
    db = load_db()
    
    if db:
        logger.info("🕒 Background Job triggered: Scanning market for price drops...")
    
    for user_id, tracked_items in db.items():
        for item in tracked_items:
            product_name = item.get("product")
            saved_alert_price = item.get("alert_price")
            
            if not product_name or not saved_alert_price:
                continue
                
            try:
                # Silently scrape the market in the background
                result = await search_jumia(product_name)
                
                if "error" not in result and result.get("valid_results_count", 0) > 0:
                    live_lowest_price = int(result['best_price'].replace(",", ""))
                    
                    if live_lowest_price < saved_alert_price:
                        # Price dropped! Fire off a Telegram DM
                        await context.bot.send_message(
                            chat_id=user_id, 
                            text=f"🚨 *PRICE DROP ALERT!* 🚨\n{product_name} just dropped to ₦{live_lowest_price:,}!\n🔗 [Buy it now]({result['best_link']})",
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                        # Update the alert price to the new lower price to prevent spam
                        item["alert_price"] = live_lowest_price
                        save_db(db)
            except Exception as e:
                logger.error(f"Background check failed for {product_name}: {e}")

def main():
    """Start the bot."""
    # Retrieve the token from environment variables
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        logger.error("No TELEGRAM_TOKEN found. Please check your .env file.")
        return

    # Create the application
    application = ApplicationBuilder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CallbackQueryHandler(button_click))

    # Schedule background job to run every hour (3600 seconds)
    application.job_queue.run_repeating(check_prices_background, interval=3600, first=10)

    logger.info("Bot is starting up...")
    
    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()
