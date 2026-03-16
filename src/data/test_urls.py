"""
Debug - Try different URLs
"""

from playwright.sync_api import sync_playwright


def test_url(url, name):
    """Test a URL."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    print(f"\n=== Testing: {name} ===")
    print(f"URL: {url}")

    try:
        response = page.goto(url, wait_until="load", timeout=15000)
        status = response.status if response else "No response"
        print(f"Status: {status}")
        print(f"Title: {page.title()[:50] if page.title() else 'N/A'}")

    except Exception as e:
        print(f"Error: {e}")

    browser.close()
    pw.stop()


def main():
    """Test different URLs."""
    urls = [
        ("https://steamdt.com", "Main page"),
        ("https://steamdt.com/market", "Market page"),
        ("https://steamdt.com/skins", "Skins page"),
        ("https://steamdt.com/skin/USP-印花集", "USP page"),
        ("https://steamdt.com/block/CSGO_Type_WeaponCase", "Weapon case"),
    ]

    for url, name in urls:
        test_url(url, name)


if __name__ == "__main__":
    main()
