"""
CS2 Market Data Scraper using Playwright (bypasses firewall)
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from typing import Optional
from playwright.sync_api import sync_playwright


class SteamDTPlaywrightScraper:
    """Scraper using Playwright to bypass firewall restrictions."""

    BASE_URL = "https://api.steamdt.com"
    API_KEY = "a91fbf9548414c779509496fd53ec2fc"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self.API_KEY
        self.playwright = None
        self.browser = None
        self.context = None

    def start(self):
        """Start Playwright browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )

    def close(self):
        """Close Playwright."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_weapon_case_kline(
        self,
        kline_type: int = 3,
        type_val: str = "CSGO_Type_WeaponCase",
        platform: str = "ALL",
    ) -> pd.DataFrame:
        """
        Fetch weapon case K-line data using Playwright.
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))

        # Use page.evaluate to make the API call
        page = self.context.new_page()

        # Set up intercept to capture response
        response_data = {}

        def handle_response(response):
            if "/user/item/block/v1/kline" in response.url:
                try:
                    response_data['data'] = response.json()
                except:
                    pass

        page.on("response", handle_response)

        # Make request through browser
        url = f"{self.BASE_URL}/user/item/block/v1/kline?timestamp={timestamp}"

        payload = {
            "type": "ITEM_TYPE",
            "klineType": kline_type,
            "maxTime": "",
            "typeVal": type_val,
            "platform": platform,
            "specialStyle": "",
            "timestamp": timestamp,
        }

        try:
            # Navigate to steamdt.com first to set cookies
            page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)

            # Make API request
            page.evaluate(f"""
                fetch('{url}', {{
                    method: 'POST',
                    headers: {{
                        'accept': 'application/json',
                        'content-type': 'application/json',
                        'Authorization': 'Bearer {self.api_key}',
                        'language': 'zh_CN',
                        'x-currency': 'CNY',
                        'x-device': '1',
                        'origin': 'https://steamdt.com',
                        'referer': 'https://steamdt.com/'
                    }},
                    body: JSON.stringify({json.dumps(payload)})
                }})
            """)

            # Wait a bit for response
            page.wait_for_timeout(3000)

        except Exception as e:
            print(f"Request error: {e}")
        finally:
            page.close()

        if response_data.get('data'):
            data = response_data['data']
            if data.get('success'):
                return self._parse_kline_data(data.get('data', []))

        return pd.DataFrame()

    def fetch_item_kline(
        self,
        item_id: str,
        kline_type: int = 3,
        platform: str = "ALL",
    ) -> pd.DataFrame:
        """
        Fetch specific item K-line data using Playwright.
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))

        page = self.context.new_page()
        response_data = {}

        def handle_response(response):
            if "/user/steam/category/v1/kline" in response.url:
                try:
                    response_data['data'] = response.json()
                except:
                    pass

        page.on("response", handle_response)

        url = f"{self.BASE_URL}/user/steam/category/v1/kline?timestamp={timestamp}&type={kline_type}&maxTime=&typeVal={item_id}&platform={platform}&specialStyle="

        try:
            page.goto("https://steamdt.com", wait_until="networkidle", timeout=30000)

            page.evaluate(f"""
                fetch('{url}', {{
                    method: 'GET',
                    headers: {{
                        'accept': '*/*',
                        'Authorization': 'Bearer {self.api_key}',
                        'language': 'zh_CN',
                        'x-currency': 'CNY',
                        'x-device': '1',
                        'origin': 'https://steamdt.com',
                        'referer': 'https://steamdt.com/'
                    }}
                }})
            """)

            page.wait_for_timeout(3000)

        except Exception as e:
            print(f"Request error: {e}")
        finally:
            page.close()

        if response_data.get('data'):
            data = response_data['data']
            if data.get('success'):
                return self._parse_kline_data(data.get('data', []))

        return pd.DataFrame()

    def _parse_kline_data(self, data: list) -> pd.DataFrame:
        """Parse K-line data into DataFrame."""
        if not data:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        records = []
        for row in data:
            if len(row) >= 5:
                records.append({
                    "date": datetime.fromtimestamp(int(row[0])),
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5] if len(row) > 5 else 0,
                })

        return pd.DataFrame(records)


# Item ID mapping
ITEM_IDS = {
    "USP-印花集": "1017617021485346816",
    "武器箱": "CSGO_Type_WeaponCase",
    "刀具": "CSGO_Type_Weapon_Knife",
    "手套": "CSGO_Type_Weapon_Gloves",
    "枪械": "CSGO_Type_Weapon",
}


def fetch_data(symbol: str = "武器箱", timeframe: str = "1d", limit: int = 100) -> dict:
    """Fetch data using Playwright."""

    tf_map = {"1m": 1, "1h": 2, "1d": 3, "1w": 4}
    kline_type = tf_map.get(timeframe, 3)

    scraper = SteamDTPlaywrightScraper()
    scraper.start()

    try:
        if symbol == "武器箱" or symbol in ITEM_IDS and ITEM_IDS.get(symbol) == "CSGO_Type_WeaponCase":
            df = scraper.fetch_weapon_case_kline(kline_type=kline_type)
        else:
            item_id = ITEM_IDS.get(symbol, symbol)
            df = scraper.fetch_item_kline(item_id=item_id, kline_type=kline_type)
    finally:
        scraper.close()

    if df.empty:
        # Fallback to mock
        from src.data.data_fetcher import fetch_mock_data
        return fetch_mock_data(symbol, timeframe, limit)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": df.to_dict("records"),
        "dataframe": df,
    }


if __name__ == "__main__":
    print("Testing Playwright scraper...")

    scraper = SteamDTPlaywrightScraper()
    scraper.start()

    try:
        print("\n1. Weapon Case (Daily):")
        df = scraper.fetch_weapon_case_kline(kline_type=3)
        print(f"Rows: {len(df)}")
        if not df.empty:
            print(df.tail(3))

        print("\n2. Weapon Case (Hourly):")
        df = scraper.fetch_weapon_case_kline(kline_type=2)
        print(f"Rows: {len(df)}")
        if not df.empty:
            print(df.tail(3))

    finally:
        scraper.close()
