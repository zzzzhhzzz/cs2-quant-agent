"""
SteamDT Item Page Scraper - Extracts all item data
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import re
from datetime import datetime


def scrape_item(url: str) -> dict:
    """
    Scrape item page and extract all data.
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()

    response = page.goto(url, wait_until="networkidle", timeout=30000)

    if response.status != 200:
        browser.close()
        pw.stop()
        return {"error": f"HTTP {response.status}"}

    page.wait_for_timeout(5000)

    # Get page text
    text = page.evaluate("document.body.innerText")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Parse data
    item_data = {
        "url": url,
        "fetch_time": datetime.now().isoformat(),
        "name": None,
        "prices": {},
        "change_today": None,
        "change_week": None,
        "change_month": None,
        "volume_today": None,
        "listings": None,
    }

    # Find item name
    for line in lines:
        if "印花集" in line and "崭新" not in line:
            item_data["name"] = line
            break

    # Parse prices - pattern is "wear_name" followed by "¥price" on next line
    wear_names = ["崭新出厂", "略有磨损", "久经沙场", "破损不堪", "战痕累累"]
    next_is_price = False

    for i, line in enumerate(lines):
        # Check if next line is price
        if line in wear_names:
            next_is_price = True
            current_wear = line
            continue

        if next_is_price and line.startswith("¥"):
            price_match = re.search(r'¥([\d,.]+)', line)
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
                item_data["prices"][current_wear] = price
            next_is_price = False
            continue

        # StatTrak
        if "StatTrak" in line:
            next_is_price = True
            current_wear = "StatTrak"
            continue

        # Find percentage changes anywhere in text
        # Format: "¥227 (+24.73%)" or "¥235(+25.82%)"
        match = re.search(r'¥[\d.]+\s*\(([+-]?[\d.]+)%\)', line)
        if match and item_data["change_today"] is None:
            item_data["change_today"] = float(match.group(1))
        elif match and item_data["change_week"] is None:
            item_data["change_week"] = float(match.group(1))
        elif match and item_data["change_month"] is None:
            item_data["change_month"] = float(match.group(1))

        # Listings
        if "存世量" in line and i + 1 < len(lines):
            match = re.search(r'([\d,]+)', lines[i + 1])
            if match:
                item_data["listings"] = int(match.group(1).replace(",", ""))

        # Today's volume
        if "今日推算成交" in line and i + 1 < len(lines):
            match = re.search(r'([\d,]+)', lines[i + 1])
            if match:
                item_data["volume_today"] = int(match.group(1).replace(",", ""))

    browser.close()
    pw.stop()

    return item_data


def scrape_multiple_items(items: list) -> pd.DataFrame:
    """Scrape multiple items."""
    results = []
    for item_url in items:
        print(f"Scraping: {item_url}")
        data = scrape_item(item_url)
        results.append(data)
    return pd.DataFrame(results)


if __name__ == "__main__":
    url = "https://steamdt.com/cs2/USP-S%20%7C%20Printstream%20(Factory%20New)"

    print("=" * 60)
    print("Scraping: USP-S | Printstream")
    print("=" * 60)

    data = scrape_item(url)

    print("\n=== Results ===")
    print(f"Name: {data.get('name')}")
    print(f"Prices: {data.get('prices')}")
    print(f"Today: {data.get('change_today')}%")
    print(f"Week: {data.get('change_week')}%")
    print(f"Month: {data.get('change_month')}%")
    print(f"Volume today: {data.get('volume_today')}")
    print(f"Listings: {data.get('listings')}")
