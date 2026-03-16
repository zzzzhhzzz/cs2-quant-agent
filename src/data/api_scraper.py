"""
SteamDT API-based Scraper
Uses the discovered APIs directly
"""

import requests
import pandas as pd
from datetime import datetime
import time


class SteamDTAPIScraper:
    """Scrape SteamDT using their API."""

    BASE_URL = "https://api.steamdt.com"
    API_KEY = "a91fbf9548414c779509496fd53ec2fc"
    ACCESS_TOKEN = "34c66bec-0fc2-43ab-ab72-2c57a1237322"

    def __init__(self, use_token: str = "access-token"):
        self.token_type = use_token  # "access-token" or "bearer"

    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        if self.token_type == "access-token":
            token = self.ACCESS_TOKEN
        else:
            token = self.API_KEY
            self.token_type = "bearer"

        return {
            "accept": "application/json",
            "content-type": "application/json",
            "language": "zh_CN",
            "x-currency": "CNY",
            "x-device": "1",
            "origin": "https://steamdt.com",
            "referer": "https://steamdt.com/",
            "Authorization": f"Bearer {token}" if self.token_type == "bearer" else None,
            "access-token": token if self.token_type == "access-token" else None,
        }

    def search_autocomplete(self, keyword: str) -> pd.DataFrame:
        """
        Get search suggestions for a keyword.

        Args:
            keyword: Search keyword

        Returns:
            DataFrame with suggestions
        """
        timestamp = int(datetime.now().timestamp() * 1000)

        url = f"{self.BASE_URL}/user/skin/v1/auto-completion"
        params = {
            "timestamp": timestamp,
            "content": keyword,
        }

        headers = self._get_headers()
        # Remove content-type for GET request
        headers.pop("content-type", None)

        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        if not data.get("success"):
            print(f"API Error: {data.get('errorMsg')}")
            return pd.DataFrame()

        items = data.get("data", [])
        df = pd.DataFrame(items)

        return df

    def search_items(self, keyword: str, page_size: int = 20) -> pd.DataFrame:
        """
        Search for items.

        Args:
            keyword: Search keyword
            page_size: Number of results

        Returns:
            DataFrame with search results
        """
        timestamp = int(datetime.now().timestamp() * 1000)

        url = f"{self.BASE_URL}/skin/market/v3/page"
        params = {"timestamp": timestamp}

        payload = {
            "dataField": "pvNums",
            "dataRange": "",
            "sortType": "desc",
            "nextId": "",
            "queryName": keyword,
            "pageSize": page_size,
            "timestamp": timestamp,
        }

        headers = self._get_headers()

        response = requests.post(url, params=params, json=payload, headers=headers)
        data = response.json()

        if not data.get("success"):
            print(f"API Error: {data.get('errorMsg')}")
            return pd.DataFrame()

        items = data.get("data", {}).get("list", [])

        # Parse items
        results = []
        for item in items:
            results.append({
                "name": item.get("name", ""),
                "price": item.get("price", 0),
                "change_pct": item.get("change", 0),
                "volume": item.get("volume", 0),
                "listings": item.get("listings", 0),
            })

        return pd.DataFrame(results)

    def get_ranking(self, app_id: int = 730) -> pd.DataFrame:
        """Get ranking data."""
        timestamp = int(datetime.now().timestamp() * 1000)

        url = f"{self.BASE_URL}/user/ranking/v1/attribute/{app_id}"
        params = {"timestamp": timestamp}

        headers = self._get_headers()
        headers.pop("content-type", None)

        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        if not data.get("success"):
            print(f"API Error: {data.get('errorMsg')}")
            return pd.DataFrame()

        return pd.DataFrame(data.get("data", []))


def main():
    """Test the scraper."""
    scraper = SteamDTAPIScraper()

    print("=" * 60)
    print("SteamDT API Scraper")
    print("=" * 60)

    # Test autocomplete
    print("\n1. Search autocomplete 'usp':")
    df = scraper.search_autocomplete("usp")
    print(f"Found {len(df)} suggestions")
    print(df.head())

    # Test search (may fail with 108 error)
    print("\n2. Search items 'usp':")
    df = scraper.search_items("usp")
    print(f"Found {len(df)} items")
    if not df.empty:
        print(df.head())

    # Test ranking
    print("\n3. Ranking data:")
    df = scraper.get_ranking()
    print(f"Found {len(df)} ranking items")
    if not df.empty:
        print(df.head())


if __name__ == "__main__":
    main()
