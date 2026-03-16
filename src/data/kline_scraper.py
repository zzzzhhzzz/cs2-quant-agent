"""
SteamDT K-Line Scraper
Uses Playwright to get K-line data from the page
"""

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime


class SteamDTKLineScraper:
    """Scrape K-line data using Playwright."""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def get_kline(self, url: str, timeframe: str = "1h") -> pd.DataFrame:
        """
        Get K-line data from item page.

        Args:
            url: SteamDT item URL
            timeframe: "1h", "4h", "1d", "1w" (currently all return same data)

        Returns:
            DataFrame with OHLCV data
        """
        context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        # Track API responses
        kline_raw = []

        def handle_response(response):
            if 'type-trend' in response.url and 'item' in response.url:
                try:
                    data = response.json()
                    if data.get('success') and data.get('data'):
                        kline_raw.extend(data['data'])
                except:
                    pass

        page.on('response', handle_response)

        # Load the page
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(5000)

        # Try to click on K-line tab
        try:
            kline_tab = page.query_selector('text=K线')
            if kline_tab:
                kline_tab.click()
                page.wait_for_timeout(3000)
        except:
            pass

        # Try to select timeframe
        tf_map = {"1h": "1小时", "4h": "4小时", "1d": "1天", "1w": "1周"}
        try:
            tf_text = tf_map.get(timeframe, "1小时")
            tf_btn = page.query_selector(f"text={tf_text}")
            if tf_btn:
                tf_btn.click()
                page.wait_for_timeout(2000)
        except:
            pass

        page.close()
        context.close()

        # Parse data
        # Format: [timestamp, hourly_open, listings, daily_high, daily_low, hourly_close, volume, id]
        # Note: row[3] is daily HIGH, row[4] is daily LOW - NOT hourly!
        # In CS2 market:
        # - "close" is the most important - actual traded price
        # - "low" (min of open/close) is more meaningful as floor price
        # - "high" has noise from high-float items, less useful
        if not kline_raw:
            return pd.DataFrame()

        records = []
        for row in kline_raw:
            if len(row) >= 6:
                try:
                    # Skip rows with None close price
                    if row[5] is None:
                        continue

                    hourly_open = float(row[1]) if row[1] else None
                    hourly_close = float(row[5]) if row[5] else None

                    # Use close as price, low as floor reference
                    hourly_low = min(hourly_open, hourly_close) if hourly_open and hourly_close else None

                    records.append({
                        "timestamp": int(row[0]),
                        "date": datetime.fromtimestamp(int(row[0])),
                        "open": hourly_open,
                        "listings": int(row[2]) if row[2] else None,
                        "high": hourly_close,  # Use close as proxy for high
                        "low": hourly_low,      # Low is more meaningful in CS2
                        "close": hourly_close,
                        "volume": float(row[6]) if len(row) > 6 and row[6] else 0,
                        "daily_high": float(row[3]) if row[3] else None,
                        "daily_low": float(row[4]) if row[4] else None,
                    })
                except (ValueError, TypeError, IndexError):
                    pass

        df = pd.DataFrame(records)
        return df


def scrape_kline(url: str, timeframe: str = "1h") -> pd.DataFrame:
    """Scrape K-line data from item URL."""
    scraper = SteamDTKLineScraper()
    scraper.start()

    try:
        df = scraper.get_kline(url, timeframe)
    finally:
        scraper.close()

    return df


if __name__ == "__main__":
    url = "https://steamdt.com/cs2/USP-S%20%7C%20Printstream%20(Factory%20New)"

    print("=" * 60)
    print("K-Line Data for USP-S | Printstream (Factory New)")
    print("=" * 60)

    df = scrape_kline(url, "1h")

    print(f"\nTotal rows: {len(df)}")
    print(f"\nLatest 10 rows:")
    print(df.tail(10).to_string())

    print(f"\nData info:")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Price range: ¥{df['low'].min():.2f} - ¥{df['high'].max():.2f}")
    print(f"  Latest price: ¥{df.iloc[-1]['close']:.2f}")
