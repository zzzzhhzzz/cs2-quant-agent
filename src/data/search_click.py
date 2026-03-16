"""
SteamDT Search Test - Click first
"""

from playwright.sync_api import sync_playwright


def main():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    print("=== Clicking on search ===")

    # Try to click on search box first
    search_selectors = [
        'input[placeholder*="搜索"]',
        '.el-input',
        '.search-input',
    ]

    for sel in search_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                print(f"Clicked: {sel}")
                page.wait_for_timeout(1000)
                break
        except:
            continue

    # Now try to type
    page.keyboard.type("武器箱", delay=100)
    page.wait_for_timeout(2000)

    # Get dropdown content
    dropdown = page.evaluate("""
        () => {
            const result = [];

            // Look for any visible popup/dropdown
            const popups = document.querySelectorAll('[class*="popup"], [class*="dropdown"], [class*="suggestion"], .el-select-dropdown, .el-autocomplete-suggestion');
            popups.forEach(p => {
                if (p.style.display !== 'none') {
                    const items = p.querySelectorAll('li, .item, [class*="item"]');
                    items.forEach(i => {
                        result.push(i.innerText.substring(0, 80));
                    });
                }
            });

            // Also check for el-autocomplete
            const autocomplete = document.querySelector('.el-autocomplete');
            if (autocomplete) {
                result.push('Found autocomplete!');
            }

            return result;
        }
    """)

    print(f"Dropdown items: {len(dropdown)}")
    for item in dropdown[:10]:
        print(f"  - {item}")

    browser.close()
    pw.stop()


if __name__ == "__main__":
    main()
