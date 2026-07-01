import logging

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from src.config import settings
from src.bot.handlers import start_command, help_command, search, button_click
from src.services.price_checker import check_prices
from src.scraper.client import browser_client

logger = logging.getLogger(__name__)


async def post_init(application):
    await browser_client.start()
    logger.info("Playwright browser started.")


async def post_stop(application):
    await browser_client.close()
    logger.info("Playwright browser closed.")


def build_application():
    if not settings.telegram_token:
        logger.error("No TELEGRAM_TOKEN found. Please check your .env file.")
        raise SystemExit(1)

    app = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(button_click))

    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(
            check_prices,
            interval=21600,
            first=10,
        )
        logger.info("Price checker scheduled every 6 hours.")

    return app
