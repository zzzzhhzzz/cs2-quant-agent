"""
CS2 Market Data Scraper for SteamDT
Based on discovered API endpoints
"""

import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any


class SteamDTScraper:
    """Scraper for SteamDT CS2 market data."""

    BASE_URL = "https://api.steamdt.com"

    # API Endpoints
    ENDPOINT_WEAPON_CASE = "/user/item/block/v1/kline"
    ENDPOINT_ITEM_KLINE = "/user/steam/category/v1/kline"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Common headers for API requests."""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "language": "zh_CN",
            "x-currency": "CNY",
            "x-device": "1",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
        }

    async def fetch_weapon_case_kline(
        self,
        kline_type: int = 3,
        type_val: str = "CSGO_Type_WeaponCase",
        platform: str = "ALL",
    ) -> pd.DataFrame:
        """
        Fetch weapon case market K-line data.

        Args:
            kline_type: 1=1min, 2=1hour, 3=1day, 4=1week
            type_val: Category type (CSGO_Type_WeaponCase, CSGO_Type_Weapon, etc.)
            platform: ALL, STEAM, BUFF163

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        session = await self._get_session()
        timestamp = str(int(datetime.now().timestamp() * 1000))

        url = f"{self.BASE_URL}{self.ENDPOINT_WEAPON_CASE}?timestamp={timestamp}"

        payload = {
            "type": "ITEM_TYPE",
            "klineType": kline_type,
            "maxTime": "",
            "typeVal": type_val,
            "platform": platform,
            "specialStyle": "",
            "timestamp": timestamp,
        }

        async with session.post(url, json=payload, headers=self._get_headers()) as response:
            data = await response.json()

            if not data.get("success"):
                print(f"API Error: {data.get('errorMsg')}")
                return pd.DataFrame()

            return self._parse_kline_data(data.get("data", []))

    async def fetch_item_kline(
        self,
        item_id: str,
        kline_type: int = 3,
        platform: str = "ALL",
        max_time: str = "",
    ) -> pd.DataFrame:
        """
        Fetch specific item K-line data.

        Args:
            item_id: SteamDT item ID (e.g., "1017617021485346816" for USP-印花集)
            kline_type: 1=1min, 2=1hour, 3=1day, 4=1week
            platform: ALL, STEAM, BUFF163
            max_time: Optional max timestamp

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        session = await self._get_session()
        timestamp = str(int(datetime.now().timestamp() * 1000))

        params = {
            "timestamp": timestamp,
            "type": kline_type,
            "maxTime": max_time,
            "typeVal": item_id,
            "platform": platform,
            "specialStyle": "",
        }

        headers = self._get_headers()
        headers["accept"] = "*/*"

        async with session.get(
            f"{self.BASE_URL}{self.ENDPOINT_ITEM_KLINE}",
            params=params,
            headers=headers,
        ) as response:
            data = await response.json()

            if not data.get("success"):
                print(f"API Error: {data.get('errorMsg')}")
                return pd.DataFrame()

            return self._parse_kline_data(data.get("data", []))

    def _parse_kline_data(self, data: list) -> pd.DataFrame:
        """
        Parse K-line data into DataFrame.

        Data format: [timestamp, open, high, low, close, volume, ...]
        """
        if not data:
            return pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "volume"]
            )

        records = []
        for row in data:
            if len(row) >= 5:
                records.append(
                    {
                        "date": datetime.fromtimestamp(int(row[0])),
                        "open": row[1],
                        "high": row[2],
                        "low": row[3],
                        "close": row[4],
                        "volume": row[5] if len(row) > 5 else 0,
                    }
                )

        df = pd.DataFrame(records)
        return df


# Item ID mapping (can be extended)
# You can get item IDs from SteamDT website or API
ITEM_IDS = {
    "USP-印花集": "1017617021485346816",
    "AK-47-红线": "3021087906",  # Example, need to verify
    "武器箱": "CSGO_Type_WeaponCase",
    "刀具": "CSGO_Type_Weapon_Knife",
    "手套": "CSGO_Type_Weapon_Gloves",
    "枪械": "CSGO_Type_Weapon",
}


async def main():
    """Test the scraper."""
    # Use your API key
    API_KEY = "a91fbf9548414c779509496fd53ec2fc"

    scraper = SteamDTScraper(API_KEY)

    print("=" * 50)
    print("Testing SteamDT Scraper")
    print("=" * 50)

    # Test weapon case K-line (1 day)
    print("\n1. Weapon Case K-line (Daily):")
    df = await scraper.fetch_weapon_case_kline(kline_type=3)
    if not df.empty:
        print(df.tail())
    else:
        print("No data returned")

    # Test weapon case K-line (1 hour)
    print("\n2. Weapon Case K-line (Hourly):")
    df = await scraper.fetch_weapon_case_kline(kline_type=2)
    if not df.empty:
        print(df.tail())
    else:
        print("No data returned")

    # Test specific item (USP-印花集)
    print("\n3. USP-印花集 K-line (Daily):")
    df = await scraper.fetch_item_kline(
        item_id="1017617021485346816", kline_type=3
    )
    if not df.empty:
        print(df.tail())
    else:
        print("No data returned")

    await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
