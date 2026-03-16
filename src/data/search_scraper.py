"""
SteamDT Search-based Scraper
Uses search functionality to get item data
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time


class SteamDTSearchScraper:
    """Scrape SteamDT using search functionality."""

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

    def search_item(self, keyword: str) -> pd.DataFrame:
        """
        Search for an item and get results.

        Args:
            keyword: Search keyword (e.g., "武器箱", "USP", "AK-47")
        """
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Searching for: {keyword}")

        # Navigate to main page
        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Find search box - try different selectors
        search_selectors = [
            'input[placeholder*="搜索"]',
            'input[class*="search"]',
            '.el-input__inner',
            'input[type="text"]',
        ]

        search_box = None
        for selector in search_selectors:
            try:
                search_box = page.query_selector(selector)
                if search_box:
                    print(f"Found search box with selector: {selector}")
                    break
            except:
                continue

        if not search_box:
            print("Search box not found!")
            page.close()
            context.close()
            return pd.DataFrame()

        # Type in search keyword
        search_box.fill(keyword)
        page.wait_for_timeout(2000)

        # Try to press Enter
        search_box.press("Enter")
        page.wait_for_timeout(3000)

        # Extract results
        results = page.evaluate("""
            () => {
                const results = [];

                // Look for search result items
                const items = document.querySelectorAll('[class*="item"], .el-autocomplete, [class*="suggest"]');
                items.forEach(item => {
                    const text = item.innerText || '';
                    if (text.trim()) {
                        results.push(text.substring(0, 200));
                    }
                });

                // Also look for table rows after search
                const tables = document.querySelectorAll('table tr');
                tables.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    if (cells.length > 0) {
                        results.push('TABLE: ' + cells.map(c => c.innerText).join(' | '));
                    }
                });

                return results;
            }
        """)

        print(f"Search results: {len(results)}")
        for r in results[:5]:
            print(f"  - {r[:100]}")

        page.close()
        context.close()

        return pd.DataFrame(results, columns=['data'])

    def get_all_categories(self) -> list:
        """Get list of all categories from the main page."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # Extract category links
        categories = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a'));
                const categories = [];

                links.forEach(link => {
                    const href = link.href || '';
                    const text = link.innerText.trim();

                    // Look for category links
                    if (href.includes('/block/') || href.includes('/category/')) {
                        categories.push({
                            text: text,
                            href: href
                        });
                    }
                });

                return categories;
            }
        """)

        page.close()
        context.close()

        return categories


def main():
    """Test the search scraper."""
    scraper = SteamDTScraper()
    scraper.start()

    try:
        print("=" * 60)
        print("Testing Search Scraper")
        print("=" * 60)

        # Get categories
        print("\n1. Categories:")
        categories = scraper.get_all_categories()
        for c in categories[:10]:
            print(f"  - {c.get('text')}: {c.get('href')}")

        # Search for weapon cases
        print("\n2. Search '武器箱':")
        scraper.search_item("武器箱")

        # Search for USP
        print("\n3. Search 'USP':")
        scraper.search_item("USP")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
