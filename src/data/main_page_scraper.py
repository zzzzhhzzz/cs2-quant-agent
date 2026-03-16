"""
Scrape data from main page using Playwright
"""

from playwright.sync_api import sync_playwright
import json


def scrape_main_page():
    """Scrape market data from main page."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    print("Loading main page...")
    page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)

    # Wait for data to load
    page.wait_for_timeout(5000)

    # Try to extract data from tables
    data = page.evaluate("""
        () => {
            const result = {};

            // 1. Look for price data in tables
            const tables = document.querySelectorAll('table');
            result.tablesFound = tables.length;

            // Sample first table
            if (tables.length > 0) {
                const firstTable = tables[0];
                const rows = Array.from(firstTable.querySelectorAll('tr'));
                result.firstTableRows = rows.length;

                // Get first few rows
                const sampleRows = [];
                rows.slice(0, 5).forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    const rowData = [];
                    cells.forEach(cell => rowData.push(cell.innerText.trim()));
                    sampleRows.push(rowData);
                });
                result.sampleRows = sampleRows;
            }

            // 2. Look for category links
            const categoryLinks = Array.from(document.querySelectorAll('a[href*="block"], a[href*="category"], a[href*="skin"]'));
            result.categoryLinks = [];
            categoryLinks.slice(0, 10).forEach(link => {
                result.categoryLinks.push({
                    href: link.href,
                    text: link.innerText.trim().substring(0, 30)
                });
            });

            return result;
        }
    """)

    print(f"\n=== Results ===")
    print(f"Tables found: {data.get('tablesFound')}")

    print(f"\nCategory Links:")
    for link in data.get('categoryLinks', [])[:5]:
        print(f"  - {link.get('text')}: {link.get('href')}")

    print(f"\nFirst table rows: {data.get('firstTableRows')}")
    for i, row in enumerate(data.get('sampleRows', [])[:3]):
        print(f"  Row {i}: {row[:5]}")  # First 5 cells

    browser.close()
    pw.stop()


if __name__ == "__main__":
    scrape_main_page()
