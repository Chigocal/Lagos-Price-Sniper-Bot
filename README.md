# 🎯 Jumia Price Sniper Bot

Telegram bot that scrapes Jumia Nigeria for the best deals, filters out accessories, verifies trusted vendors, and sends price-drop alerts.

## ✨ Features

- 🧠 **AI Query Correction** — Gemini 2.5 Flash fixes typos and standardizes search queries
- 🛡️ **Smart Filtering** — Removes accessories (cases, screen protectors, etc.) and price outliers
- ✅ **Trust Verification** — Detects "Official Store" and "Express" badges, prioritizes trusted vendors
- 📊 **Market Analysis** — Returns listing count, price range, and the best trusted deal
- 🔔 **Price Tracking** — Click "Track Price Drops" to get notified when prices fall below your alert threshold
- 🚀 **Persistent Browser** — Playwright Chromium stays alive across searches (much faster)
- ⚡ **Parallel Extraction** — Product cards scraped concurrently with `asyncio.gather`
- 💾 **Search Cache** — Gemini results cached to disk so repeated queries skip the API call

## 🛠️ Requirements

- Python 3.11+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- (Optional) Gemini API key for query correction

## ⚙️ Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Create a `.env` file:

```env
TELEGRAM_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
```

## 🎮 Usage

```bash
python -m src.main
```

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help`  | Command reference |
| `/search iPhone 15` | Search and analyze Jumia listings |

After a search, click **Track Price Drops** to save the product. The bot will alert you if the price drops below the tracked amount.

## 📁 Project Layout

```
src/
├── main.py               # Entry point
├── config.py             # pydantic-settings config from .env
├── bot/
│   ├── app.py            # Bot setup + polling + recurring jobs
│   └── handlers.py       # Command + callback handlers
├── scraper/
│   ├── client.py         # Persistent Playwright browser
│   ├── jumia.py          # Jumia search + price extraction
│   └── cache.py          # Gemini query cache (JSON)
├── services/
│   ├── search.py         # Orchestrator (clean → scrape → return)
│   ├── query_cleaner.py  # Gemini AI integration
│   └── price_checker.py  # Background price monitoring
└── database/
    ├── interface.py      # Abstract database interface
    ├── json_db.py        # JSON file implementation
    └── postgres.py       # PostgreSQL stub (ready to swap)
data/
├── database.json         # Tracked products
└── search_cache.json     # Gemini cache
tests/                    # pytest test suite
```

## 🚨 Price Alerts

The bot checks every 6 hours. If the current Jumia price is lower than your tracked alert price, you'll receive a message like:

> Price Drop Alert!
> Redmi 13C
> Was: 190,000
> Now: 150,000
> [View on Jumia](...)

The alert price updates to the new lower price so you're only notified about fresh drops.
