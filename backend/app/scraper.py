import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_website_basic(url: str) -> str:
    """Basic scripting - just get the HTML structure"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = await page.content()

            # Clean up HTML
            soup = BeautifulSoup(content, 'html.parser')

            # Remove scripts and make safe
            for script in soup(["script", "style"]):
                script.decompose()

            return str(soup)

        finally:
            await browser.close()
