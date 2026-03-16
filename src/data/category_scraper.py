"""
SteamDT Category Scraper
"""

from playwright.sync_api import sync_playwright
import pandas as pd


class SteamDTCategoryScraper:
    """Scrape different categories from SteamDT."""

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

    def try_category_url(self, url: str, name: str) -> dict:
        """Try to access a category URL."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"\nTrying: {name} ({url})")

        try:
            response = page.goto(url, wait_until="load", timeout=15000)
            status = response.status if response else "No response"

            print(f"  Status: {status}")

            if status == 200:
                page.wait_for_timeout(3000)

                # Try to get table data
                tables = page.query_selector_all('table')
                print(f"  Tables: {len(tables)}")

                if tables:
                    data = page.evaluate("""
                        () => {
                            const tables = document.querySelectorAll('table');
                            const rows = tables[0].querySelectorAll('tr');
                            const result = [];
                            rows.slice(0, 10).forEach(row => {
                                const cells = row.querySelectorAll('td');
                                if (cells.length > 0) {
                                    result.push(cells[1].innerText.split('\\n')[0]);
                                }
                            });
                            return result;
                        }
                    """)
                    print(f"  Items: {data[:5]}")

                return {'status': status, 'tables': len(tables)}

        except Exception as e:
            print(f"  Error: {str(e)[:50]}")
            return {'error': str(e)[:50]}

        page.close()
        context.close()

        return {'status': status}


def main():
    scraper = SteamDTCategoryScraper()
    scraper.start()

    try:
        # Try various URLs
        urls = [
            ("https://steamdt.com/block", "block"),
            ("https://steamdt.com/case", "case"),
            ("https://steamdt.com/weapon", "weapon"),
            ("https://steamdt.com/skin", "skin"),
            ("https://steamdt.com/category", "category"),
            ("https://steamdt.com/market", "market"),
            ("https://steamdt.com/cs2", "cs2"),
            ("https://steamdt.com/items", "items"),
            ("https://steamdt.com/", "main"),
        ]

        for url, name in urls:
            scraper.try_category_url(url, name)

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
