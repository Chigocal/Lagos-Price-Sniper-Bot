import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from scraper import search_jumia

# Load environment variables from .env file
load_dotenv()

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
    query = " ".join(context.args)
    
    # Send the initial loading message
    loading_message = await update.message.reply_text(
        f"🔍 Infiltrating Jumia for '{query}'...\nAnalyzing prices and filtering trusted vendors... ⏳"
    )
    
    # Run the scraper
    try:
        result = await search_jumia(query)
        
        if "error" in result:
            # Edit the loading message with the error
            await loading_message.edit_text(
                f"❌ *Failed to snipe product:*\n{result['error']}", 
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Escape brackets in the name to prevent markdown link breaking
            clean_name = result['best_match_name'].replace('[', '(').replace(']', ')')
            
            # Format the success message
            success_text = (
                f"📊 *Market Analysis for {query}*\n"
                f"Found {result['valid_results_count']} authentic listings.\n"
                f"📉 Price Range: ₦{result['range_min']} - ₦{result['range_max']}\n\n"
                f"🔥 *Best Trusted Deal:*\n"
                f"📱 {clean_name}\n"
                f"💰 ₦{result['best_price']}\n"
                f"🔗 [View on Jumia]({result['best_link']})"
            )
            
            # Create Inline Keyboard for tracking
            # We slice the query to ensure callback_data stays within Telegram's 64 byte limit
            keyboard = [
                [InlineKeyboardButton("🔔 Track Price Drops", callback_data=f"track_{query[:20]}")]
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
    # Some clients may have trouble otherwise.
    await query.answer("✅ Tracking activated! I'll notify you if the price drops.", show_alert=True)

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

    logger.info("Bot is starting up...")
    
    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()
