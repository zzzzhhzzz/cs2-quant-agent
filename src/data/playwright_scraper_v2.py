"""
CS2 Market Data Scraper using Playwright - Direct page scraping
"""

import json
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright


class SteamDTPlaywrightScraper:
    """Scraper using Playwright to directly parse page data."""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def start(self):
        """Start Playwright browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def close(self):
        """Close Playwright."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_weapon_case_kline(self, kline_type: int = 3) -> pd.DataFrame:
        """
        Fetch weapon case K-line by visiting the category page.
        """
        page = self.browser.new_page()

        # Map kline_type to URL
        # 1 = 1min, 2 = 1hour, 3 = 1day, 4 = 1week
        type_map = {1: "1m", 2: "1h", 3: "1d", 4: "1w"}
        timeframe = type_map.get(kline_type, "1d")

        try:
            # Navigate to weapon case page
            url = f"https://steamdt.com/block/CSGO_Type_WeaponCase"
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for chart to load
            page.wait_for_timeout(2000)

            # Try to find K-line data in page
            # The data is usually in window.__INITIAL_STATE__ or similar
            kline_data = page.evaluate("""
                () => {
                    // Try different ways to get kline data
                    const data = {};

                    // Check for global data
                    if (window.__INITIAL_STATE__) {
                        data.initialState = window.__INITIAL_STATE__;
                    }
                    if (window.__STORE__) {
                        data.store = window.__STORE__;
                    }

                    // Look for kline chart element
                    const chartEl = document.querySelector('[class*="kline"]');
                    if (chartEl) {
                        data.chartFound = true;
                    }

                    // Get all script content
                    const scripts = document.querySelectorAll('script');
                    const klineScripts = [];
                    scripts.forEach(s => {
                        const content = s.textContent || '';
                        if (content.includes('kline') || content.includes('KLine')) {
                            klineScripts.push(content.substring(0, 500));
                        }
                    });
                    data.klineScripts = klineScripts;

                    return data;
                }
            """)

            print(f"Kline data found: {len(kline_data.get('klineScripts', []))} script(s)")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            page.close()

        return pd.DataFrame()

    def fetch_item_kline(self, item_name: str, kline_type: int = 3) -> pd.DataFrame:
        """
        Fetch specific item K-line by visiting item page.
        """
        page = self.browser.new_page()

        # URL encode item name
        import urllib.parse
        encoded_name = urllib.parse.quote(item_name)

        try:
            url = f"https://steamdt.com/skin/{encoded_name}"
            page.goto(url, wait_until="networkidle", timeout=30000)

            page.wait_for_timeout(2000)

            # Try to extract data
            result = page.evaluate(f"""
                () => {{
                    const data = {{}};

                    // Look for __INITIAL_STATE__
                    const scripts = document.querySelectorAll('script');
                    for (const s of scripts) {{
                        const text = s.textContent || '';
                        if (text.includes('__INITIAL_STATE__')) {{
                            try {{
                                const match = text.match(/__INITIAL_STATE__\\s*=\\s*({{.+?}})/);
                                if (match) {{
                                    data.state = JSON.parse(match[1]);
                                }}
                            }} catch(e) {{}}
                        }}
                        if (text.includes('kline') || text.includes('KLine')) {{
                            data.hasKline = true;
                            // Extract kline array
                            const klineMatch = text.match(/kline[^=]*=\\s*\\[([^\\]]+)/);
                            if (klineMatch) {{
                                data.klineRaw = klineMatch[0].substring(0, 200);
                            }}
                        }}
                    }}

                    return data;
                }}
            """)

            print(f"Item: {item_name}, Data: {result}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            page.close()

        return pd.DataFrame()


def test_playwright():
    """Test Playwright directly on the website."""
    scraper = SteamDTPlaywrightScraper()
    scraper.start()

    try:
        print("=" * 60)
        print("Testing Playwright on SteamDT")
        print("=" * 60)

        # Test 1: Visit main page
        print("\n1. Main page:")
        page = scraper.browser.new_page()
        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        print(f"Title: {page.title()}")
        page.close()

        # Test 2: Weapon case page
        print("\n2. Weapon case page:")
        df = scraper.fetch_weapon_case_kline(kline_type=3)
        print(f"Rows: {len(df)}")

        # Test 3: USP page
        print("\n3. USP-印花集 page:")
        df = scraper.fetch_item_kline("USP-印花集", kline_type=3)
        print(f"Rows: {len(df)}")

    finally:
        scraper.close()


if __name__ == "__main__":
    test_playwright()
