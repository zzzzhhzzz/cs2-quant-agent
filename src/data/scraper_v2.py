"""
SteamDT Scraper - Try to get more data
"""

from playwright.sync_api import sync_playwright
import pandas as pd


class SteamDTScraperV2:
    """Enhanced scraper for SteamDT."""

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

    def get_all_tables(self) -> pd.DataFrame:
        """Get all data from tables on the page."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(5000)

        # Try to scroll down to load more data
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(2000)

        # Get all tables
        tables_data = page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const result = [];

                tables.forEach((table, tableIndex) => {
                    const rows = table.querySelectorAll('tr');
                    rows.forEach((row, rowIndex) => {
                        const cells = row.querySelectorAll('td, th');
                        const rowData = [];
                        cells.forEach(cell => {
                            rowData.push(cell.innerText.trim());
                        });
                        if (rowData.length > 0) {
                            result.push({
                                table: tableIndex,
                                row: rowIndex,
                                data: rowData
                            });
                        }
                    });
                });

                return result;
            }
        """)

        page.close()
        context.close()

        return pd.DataFrame(tables_data)

    def click_and_expand(self) -> None:
        """Try clicking on elements to expand data."""
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # Try to find and click "加载更多" (load more) buttons
        load_more = page.query_selector_all('button:has-text("加载更多"), a:has-text("加载更多"), .el-button:has-text("更多")')

        print(f"Found {len(load_more)} 'load more' elements")

        if load_more:
            try:
                load_more[0].click()
                page.wait_for_timeout(3000)
                print("Clicked load more!")
            except Exception as e:
                print(f"Click error: {e}")

        # Try to find category menu/tabs
        tabs = page.query_selector_all('.el-tabs__item, [class*="tab"], [class*="category"]')
        print(f"Found {len(tabs)} tabs/categories")

        page.close()
        context.close()


def main():
    scraper = SteamDTScraperV2()
    scraper.start()

    try:
        print("=== Getting all tables ===")
        df = scraper.get_all_tables()
        print(f"Total rows: {len(df)}")

        # Show unique tables
        tables = df['table'].unique()
        print(f"Number of tables: {len(tables)}")

        for t in tables:
            table_data = df[df['table'] == t]
            print(f"\n=== Table {t} ({len(table_data)} rows) ===")
            for _, row in table_data.head(5).iterrows():
                print(f"  {row['data'][:4]}")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
