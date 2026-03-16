"""
CS2 Market Data Scraper using Playwright - Network interception
"""

import json
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright


class SteamDTPlaywrightScraper:
    """Scraper using Playwright network interception."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.api_data = {}

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

    def fetch_kline(self, item_path: str, kline_type: int = 3) -> pd.DataFrame:
        """
        Fetch K-line by intercepting network requests.

        Args:
            item_path: URL path like "block/CSGO_Type_WeaponCase" or "skin/USP-印花集"
            kline_type: 1=1m, 2=1h, 3=1d, 4=1w
        """
        self.api_data = {}

        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Set up response interceptor
        def handle_response(response):
            url = response.url
            if "kline" in url or "category" in url or "block" in url:
                try:
                    data = response.json()
                    self.api_data[url] = data
                except:
                    pass

        page.on("response", handle_response)

        # Navigate to page
        url = f"https://steamdt.com/{item_path}"
        print(f"Navigating to: {url}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for initial load
            page.wait_for_timeout(3000)

            # Try to click on different timeframe tabs
            # Common tab selectors
            timeframe_selectors = [
                'button:has-text("1分")', 'button:has-text("1小时")',
                'button:has-text("1天")', 'button:has-text("1周")',
                '[class*="time"]:has-text("1")',
                '.el-button:has-text("1")',
                'div:has-text("1小时")', 'div:has-text("1天")',
            ]

            # Wait more for data to load
            page.wait_for_timeout(5000)

            print(f"Captured {len(self.api_data)} API responses")
            for url, data in self.api_data.items():
                print(f"  - {url}")
                if data.get('success'):
                    print(f"    Success! Data rows: {len(data.get('data', []))}")
                    return self._parse_kline_data(data.get('data', []))

        except Exception as e:
            print(f"Error: {e}")
        finally:
            page.close()
            context.close()

        return pd.DataFrame()

    def fetch_weapon_case_kline(self, kline_type: int = 3) -> pd.DataFrame:
        """Fetch weapon case K-line."""
        return self.fetch_kline("block/CSGO_Type_WeaponCase", kline_type)

    def fetch_item_kline(self, item_name: str, kline_type: int = 3) -> pd.DataFrame:
        """Fetch specific item K-line."""
        import urllib.parse
        encoded = urllib.parse.quote(item_name)
        return self.fetch_kline(f"skin/{encoded}", kline_type)

    def _parse_kline_data(self, data: list) -> pd.DataFrame:
        """Parse K-line data into DataFrame."""
        if not data:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        records = []
        for row in data:
            if len(row) >= 5:
                try:
                    records.append({
                        "date": datetime.fromtimestamp(int(row[0])),
                        "open": float(row[1]),
                        "high": float(row[2]),
                        "low": float(row[3]),
                        "close": float(row[4]),
                        "volume": float(row[5]) if len(row) > 5 else 0,
                    })
                except (ValueError, TypeError) as e:
                    print(f"Parse error: {e}, row: {row}")

        return pd.DataFrame(records)


def test():
    """Test the scraper."""
    scraper = SteamDTPlaywrightScraper()
    scraper.start()

    try:
        print("=" * 60)
        print("Testing Playwright Network Interception")
        print("=" * 60)

        print("\n1. Weapon Case (Daily):")
        df = scraper.fetch_weapon_case_kline(kline_type=3)
        print(f"Rows: {len(df)}")
        if not df.empty:
            print(df.tail(3))

        print("\n2. USP-印花集 (Daily):")
        df = scraper.fetch_item_kline("USP-印花集", kline_type=3)
        print(f"Rows: {len(df)}")
        if not df.empty:
            print(df.tail(3))

    finally:
        scraper.close()


if __name__ == "__main__":
    test()
