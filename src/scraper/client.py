import asyncio
from playwright.async_api import async_playwright, Browser, Playwright


class BrowserClient:
    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._browser:
                return
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

    async def get_browser(self) -> Browser:
        if not self._browser:
            await self.start()
        return self._browser

    async def close(self):
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None


browser_client = BrowserClient()
