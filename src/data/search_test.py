"""
SteamDT Search Test
"""

from playwright.sync_api import sync_playwright
import pandas as pd


class SteamDTSearchTest:
    """Test search functionality."""

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

    def test_search(self, keyword: str):
        """Test search for a keyword."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        print(f"\n=== Searching: {keyword} ===")

        # Find search input - try various selectors
        search_input = None
        selectors = [
            'input[placeholder*="搜索"]',
            'input[placeholder*="Search"]',
            'input[type="search"]',
            '.el-input__inner',
            'input.el-input__inner',
        ]

        for sel in selectors:
            search_input = page.query_selector(sel)
            if search_input:
                print(f"Found search input: {sel}")
                break

        if not search_input:
            print("Search input not found!")
            page.close()
            context.close()
            return

        # Type keyword
        search_input.fill(keyword)
        page.wait_for_timeout(2000)

        # Look for dropdown/suggestions
        dropdown = page.evaluate("""
            () => {
                // Look for autocomplete dropdown
                const suggestions = document.querySelectorAll('[class*="suggest"], [class*="autocomplete"], .el-autocomplete-suggestion');
                const result = [];

                suggestions.forEach(s => {
                    const items = s.querySelectorAll('li, .item');
                    items.forEach(item => {
                        result.push(item.innerText.substring(0, 100));
                    });
                });

                return result;
            }
        """)

        print(f"Dropdown items: {len(dropdown)}")
        for item in dropdown[:10]:
            print(f"  - {item}")

        # Press key to select
        search_input.press("Enter")
        page.wait_for_timeout(3000)

        print(f"After enter, URL: {page.url}")

        page.close()
        context.close()


def main():
    scraper = SteamDTSearchTest()
    scraper.start()

    try:
        scraper.test_search("武器箱")
        scraper.test_search("USP")
        scraper.test_search("AK-47")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
