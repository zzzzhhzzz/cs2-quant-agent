"""
Debug Playwright - see all network requests
"""

from playwright.sync_api import sync_playwright
import json


def main():
    """Debug network requests."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    all_requests = []
    all_responses = []

    def log_request(request):
        all_requests.append({
            'url': request.url,
            'method': request.method,
        })

    def log_response(response):
        try:
            all_responses.append({
                'url': response.url,
                'status': response.status,
            })
        except:
            pass

    page.on("request", log_request)
    page.on("response", log_response)

    print("Loading page...")

    # Try to load the weapon case page
    page.goto("https://steamdt.com/block/CSGO_Type_WeaponCase", wait_until="load", timeout=30000)
    page.wait_for_timeout(5000)

    print(f"\nTotal requests: {len(all_requests)}")
    print(f"Total responses: {len(all_responses)}")

    # Show all API-like requests
    print("\n--- API-like requests (containing 'api' or 'kline' or 'steamdt'): ---")
    for req in all_requests:
        url = req['url']
        if 'api' in url.lower() or 'kline' in url.lower() or 'steamdt' in url.lower():
            print(f"  {req['method']} {url}")

    print("\n--- All response statuses: ---")
    status_count = {}
    for resp in all_responses:
        status = resp['status']
        status_count[status] = status_count.get(status, 0) + 1
    print(status_count)

    # Print some example URLs
    print("\n--- Sample URLs ---")
    for req in all_requests[:10]:
        print(f"  {req['method']} {req['url'][:100]}")

    browser.close()
    pw.stop()


if __name__ == "__main__":
    main()
