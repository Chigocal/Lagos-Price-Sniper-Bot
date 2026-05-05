# 🎯 Jumia Price Sniper Bot

An advanced, asynchronous Telegram AI bot engineered to help users find the absolute best deals on Jumia Nigeria. Built with `python-telegram-bot` and `playwright`, it automatically scrapes search results, intelligently filters out irrelevant accessories (like phone cases when you're looking for a phone), and presents a clean, Markdown-formatted market analysis directly in Telegram.

## ✨ Features

- **Asynchronous Scraping:** Uses Playwright to spin up a headless Chromium instance, ensuring dynamic content from Jumia loads perfectly.
- **Intelligent Filtering System:** Dynamically calculates maximum prices to exclude suspiciously cheap outliers (e.g., ₦5,000 cases mixed into ₦500,000 phone results). It also features keyword-based filtering to ignore cases, screen protectors, and pouches.
- **Trust Verification:** Scans the DOM for Jumia's "Official Store" and "Express" badges, prioritizing trusted vendors for the final recommendation.
- **Market Analysis UI:** Returns the total count of valid authentic listings, the market price range (Min-Max), and highlighting the absolute best deal.
- **Interactive Buttons:** Uses Telegram's Inline Keyboards to allow users to subscribe to price drops for their searched items.y

## 🛠️ Requirements

- Python 3.8+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Libraries Used
- `python-telegram-bot` (v20+)
- `playwright`
- `python-dotenv`

## 🚀 Installation & Setup

1. **Clone the repository** (or download the files).
2. **Install the required Python packages:**
   ```bash
   pip install python-telegram-bot playwright python-dotenv
   ```
3. **Install the Playwright browser binaries:**
   ```bash
   playwright install chromium
   ```
4. **Set up your Environment Variables:**
   - Create a file named `.env` in the root directory.
   - Add your Telegram token:
     ```env
     TELEGRAM_TOKEN=your_bot_token_here
     ```

## 🎮 Usage

Start the bot engine by running:
```bash
python main.py
```

Once running, head over to your bot in Telegram and use the following commands:
- `/start` - Initializes the bot and displays the AI welcome message.
- `/help` - Brings up the user manual and feature instructions.
- `/search <product name>` - Triggers the web scraper to run a deep analysis on Jumia (e.g., `/search iPhone 15 Pro`).

## 📁 File Structure

- `main.py` - The primary Telegram Bot controller. Handles routing, UI rendering, and user interactions.
- `scraper.py` - The Playwright engine. Handles the headless browser automation, DOM parsing, and price mathematics.
- `.env` - (Not included in repo) Your secret keys.
- `.gitignore` - Prevents sensitive data and bloated caches from being pushed to version control.
