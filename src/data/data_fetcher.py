"""CS2 Market Data Fetcher - Integrated with SteamDT API."""

import pandas as pd
from datetime import datetime
from typing import Optional

# Try to import API scraper
try:
    from src.data.api_scraper import SteamDTAPIScraper
    API_SCRAPER_AVAILABLE = True
except ImportError:
    API_SCRAPER_AVAILABLE = False


def fetch_data(
    symbol: str = "market",
    timeframe: str = "1d",
    limit: int = 100,
) -> dict:
    """
    Fetch market data for CS2 items.

    Args:
        symbol: Search keyword (e.g., "market", "武器箱", "USP", "AK-47")
        timeframe: Not used
        limit: Number of items to fetch

    Returns:
        Dictionary with market data and DataFrame
    """
    if not API_SCRAPER_AVAILABLE:
        return fetch_mock_data(symbol, timeframe, limit)

    try:
        scraper = SteamDTAPIScraper()

        # Use search autocomplete to get items
        df = scraper.search_autocomplete(symbol)

        if not df.empty:
            # Add fetch time
            df['fetch_time'] = datetime.now()

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "data": df.to_dict("records"),
                "dataframe": df,
            }

    except Exception as e:
        print(f"API error: {e}")

    # Fallback to mock
    return fetch_mock_data(symbol, timeframe, limit)


def fetch_mock_data(symbol: str, timeframe: str, limit: int) -> dict:
    """Generate mock data when API is unavailable."""
    import random
    from datetime import timedelta

    base_price = 2500.0
    data = []
    now = datetime.now()

    tf_hours = {"1m": 1/60, "1h": 1, "4h": 4, "1d": 24, "1w": 168}
    hours_step = tf_hours.get(timeframe, 1)

    for i in range(limit):
        timestamp = now - timedelta(hours=int((limit - i) * hours_step))
        open_price = base_price + random.uniform(-50, 50)
        close_price = open_price + random.uniform(-30, 30)
        high_price = max(open_price, close_price) + random.uniform(0, 20)
        low_price = min(open_price, close_price) - random.uniform(0, 20)
        volume = random.randint(1000, 10000)

        data.append({
            "timestamp": timestamp.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
            "date": timestamp,
        })

        base_price = close_price

    df = pd.DataFrame(data)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": data,
        "dataframe": df,
    }


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("Testing fetch_data")
    print("=" * 60)

    # Test with different keywords
    for keyword in ["武器箱", "AK-47", "USP", "刀"]:
        result = fetch_data(keyword, "1d", 20)
        print(f"\n{keyword}: {len(result['dataframe'])} items")
        print(result['dataframe'].head(3).to_string())
