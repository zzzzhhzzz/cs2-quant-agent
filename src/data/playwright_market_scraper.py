"""
SteamDT Market Data Scraper using Playwright
"""

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import re


class SteamDTScraper:
    """Scrape CS2 market data from SteamDT using Playwright."""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def start(self):
        """Start Playwright."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def close(self):
        """Close Playwright."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_market_data(self, max_items: int = 50) -> pd.DataFrame:
        """
        Fetch current market data from main page.

        Returns:
            DataFrame with columns: name, price, change_pct, volume, listings
        """
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Loading SteamDT main page...")
        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # Extract data from table
        raw_data = page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const result = [];

                if (tables.length > 0) {
                    const firstTable = tables[0];
                    const rows = Array.from(firstTable.querySelectorAll('tr'));

                    rows.forEach(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        if (cells.length >= 4) {
                            result.push(cells.map(c => c.innerText));
                        }
                    });
                }
                return result;
            }
        """)

        # Parse the data
        items = []
        for row in raw_data[:max_items]:
            if len(row) < 4:
                continue

            # Row format: [checkbox, name+price, change+stats, update_time]
            # cell[1] contains: "沙漠之鹰 | 午夜凶匪 (崭新出厂)\n¥1050\n价格涨幅: + 37.08%..."
            # cell[2] contains: "+37.08%(¥284)\n¥766 >> ¥ 1050"

            # Extract name and price from cell 1
            cell1 = row[1] if len(row) > 1 else ""
            lines1 = cell1.split('\n')
            name = lines1[0].strip() if lines1 else ""

            price = None
            if len(lines1) > 1:
                price_match = re.search(r'¥?([\d,.]+)', lines1[1])
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))

            # Extract change from cell 2
            cell2 = row[2] if len(row) > 2 else ""

            change_pct = None
            change_match = re.search(r'([+-]?[\d.]+)%', cell2)
            if change_match:
                change_pct = float(change_match.group(1))

            volume = None
            volume_match = re.search(r'成交量[:\s]*[+-]?[\d.]+%\s*([\d,]+)', cell2)
            if volume_match:
                volume = int(volume_match.group(1).replace(',', ''))

            listings = None
            listings_match = re.search(r'在售数[:\s]*[+-]?[\d.]+%\s*([\d,]+)', cell2)
            if listings_match:
                listings = int(listings_match.group(1).replace(',', ''))

            items.append({
                'name': name,
                'price': price,
                'change_pct': change_pct,
                'volume': volume,
                'listings': listings,
                'fetch_time': datetime.now()
            })

        page.close()
        context.close()

        return pd.DataFrame(items)

    def fetch_category_data(self, category_url: str) -> pd.DataFrame:
        """
        Fetch data for a specific category.

        Args:
            category_url: URL path like "block/CSGO_Type_WeaponCase"
        """
        # Note: Direct category URLs may return 500 errors
        # This is a placeholder for when they work
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        url = f"https://steamdt.com/{category_url}"
        print(f"Loading {url}...")

        try:
            response = page.goto(url, wait_until="load", timeout=15000)
            if response.status != 200:
                print(f"Warning: Status {response.status}")
                page.close()
                context.close()
                return pd.DataFrame()

            page.wait_for_timeout(3000)

            # Try to extract similar to main page
            # Note: This may need adjustment for category pages

        except Exception as e:
            print(f"Error: {e}")

        page.close()
        context.close()

        return pd.DataFrame()


# Integration with existing data_fetcher
def fetch_data(symbol: str = "market", timeframe: str = "1d", limit: int = 100) -> dict:
    """
    Fetch market data (integrated with existing code).
    """
    scraper = SteamDTScraper()
    scraper.start()

    try:
        df = scraper.fetch_market_data(max_items=limit)
    finally:
        scraper.close()

    if df.empty:
        from src.data.data_fetcher import fetch_mock_data
        return fetch_mock_data(symbol, timeframe, limit)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": df.to_dict("records"),
        "dataframe": df,
    }


def main():
    """Test the scraper."""
    scraper = SteamDTScraper()
    scraper.start()

    try:
        print("=" * 60)
        print("SteamDT Market Data Scraper")
        print("=" * 60)

        df = scraper.fetch_market_data(max_items=20)

        print(f"\nFetched {len(df)} items")
        print("\nDataFrame:")
        print(df.to_string())

        # Save to CSV
        df.to_csv("steamdt_market_data.csv", index=False, encoding='utf-8-sig')
        print("\nSaved to steamdt_market_data.csv")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
