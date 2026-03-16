"""
SteamDT Comprehensive Scraper
"""

from playwright.sync_api import sync_playwright
import pandas as pd


class SteamDTScraper:
    """Comprehensive scraper for SteamDT."""

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

    def get_page_data(self) -> dict:
        """Get all interesting data from the page."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # Get all links
        data = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a'));

                const result = {
                    allLinks: [],
                    categoryLinks: [],
                    skinLinks: [],
                    blockLinks: [],
                };

                links.forEach(link => {
                    const href = link.href || '';
                    const text = link.innerText.trim().substring(0, 50);

                    result.allLinks.push({ href, text });

                    if (href.includes('/skin/') || href.includes('/item/')) {
                        result.skinLinks.push({ href, text });
                    }
                    if (href.includes('/block/')) {
                        result.blockLinks.push({ href, text });
                    }
                    if (href.includes('/category/')) {
                        result.categoryLinks.push({ href, text });
                    }
                });

                return result;
            }
        """)

        page.close()
        context.close()

        return data

    def search_and_get_results(self, keyword: str) -> pd.DataFrame:
        """Search and capture the autocomplete/suggestion results."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Set up listener for network requests
        api_calls = []

        def handle_response(response):
            url = response.url
            if 'search' in url.lower() or 'suggest' in url.lower() or 'api' in url.lower():
                try:
                    api_calls.append({'url': url, 'data': response.json()})
                except:
                    pass

        page.on("response", handle_response)

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Try to find and use search
        try:
            # Find search input
            search_input = page.query_selector('input')
            if search_input:
                search_input.fill(keyword)
                page.wait_for_timeout(2000)

                # Press down arrow to select first result
                search_input.press("ArrowDown")
                page.wait_for_timeout(1000)
                search_input.press("Enter")
                page.wait_for_timeout(3000)

                print(f"After search, URL: {page.url}")
        except Exception as e:
            print(f"Search error: {e}")

        # Get API calls
        print(f"\nAPI calls captured: {len(api_calls)}")
        for call in api_calls[:5]:
            print(f"  - {call['url'][:80]}")

        page.close()
        context.close()

        return pd.DataFrame()


def main():
    scraper = SteamDTScraper()
    scraper.start()

    try:
        print("=== Getting all links ===")
        data = scraper.get_page_data()

        print(f"\nTotal links: {len(data['allLinks'])}")
        print(f"Block links: {len(data['blockLinks'])}")
        print(f"Skin links: {len(data['skinLinks'])}")

        print("\n=== Block Links ===")
        for link in data['blockLinks'][:10]:
            print(f"  - {link['text']}: {link['href']}")

        print("\n=== Skin Links (sample) ===")
        for link in data['skinLinks'][:10]:
            print(f"  - {link['text']}: {link['href']}")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
