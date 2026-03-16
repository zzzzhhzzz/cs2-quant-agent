"""
CS2-Specific Indicators Module
Calculate indicators tailored for CS2 market characteristics:
- 7-day trade cooldown (no T+0)
- Low volume environment
- High volatility

Removed traditional indicators (MACD, RSI, Bollinger Bands) that don't apply to CS2 market.
"""

import pandas as pd
import numpy as np


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate CS2-specific technical indicators using pandas

    Args:
        df: DataFrame with columns ['date', 'open', 'listings', 'low', 'volume']

    Returns:
        DataFrame with added CS2-specific indicator columns
    """
    result = df.copy()

    # Drop rows with NaN in essential columns
    result = result.dropna(subset=['low', 'open', 'listings'])
    result = result.reset_index(drop=True)

    # In CS2 market, use "low" (floor price) as primary price
    price_col = 'low'

    # MA (Moving Average) - keep only 7, 30, 60 for long-term trend
    for period in [7, 30, 60]:
        result[f'MA_{period}'] = result[price_col].rolling(window=period).mean()

    # Deviation indicators (price vs moving averages)
    # Shows how overvalued/undervalued the current price is
    result['Deviation_7d'] = (result[price_col] / result['MA_7'] - 1) * 100
    result['Deviation_30d'] = (result[price_col] / result['MA_30'] - 1) * 100
    result['Deviation_60d'] = (result[price_col] / result['MA_60'] - 1) * 100

    # Listings Trend: compare recent 7 days vs previous 7 days
    # Indicates supply changes in the market
    result['Listings_MA_7'] = result['listings'].rolling(window=7).mean()
    result['Listings_MA_7_prev'] = result['listings'].shift(7).rolling(window=7).mean()
    result['Listings_Trend'] = ((result['Listings_MA_7'] / result['Listings_MA_7_prev']) - 1) * 100

    # Volume Health: avg volume / avg listings (liquidity indicator)
    # High ratio = healthy liquidity, low ratio = illiquid
    result['Volume_MA_7'] = result['volume'].rolling(window=7).mean()
    result['Volume_Health'] = result['Volume_MA_7'] / result['Listings_MA_7']

    # Volatility: 30-day rolling standard deviation
    # Shows risk level - high volatility = high risk
    result['Returns'] = result[price_col].pct_change()
    result['Volatility_30d'] = result['Returns'].rolling(window=30).std() * 100

    # Keep MA5 for short-term reference (but don't emphasize it)
    result['MA_5'] = result[price_col].rolling(window=5).mean()

    return result


def extract_features(df: pd.DataFrame) -> str:
    """
    Extract key CS2-specific features and generate structured text payload

    Args:
        df: DataFrame with CS2-specific indicators calculated

    Returns:
        Structured text string with key features
    """
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    features = []

    # Price and MA analysis (use "low" as floor price)
    features.append("=== Price & Moving Averages (Based on Floor Price) ===")
    features.append(f"Floor Price (Low): {latest['low']:.2f}")
    features.append(f"MA7: {latest['MA_7']:.2f}")
    features.append(f"MA30: {latest['MA_30']:.2f}")
    features.append(f"MA60: {latest['MA_60']:.2f}")

    # Deviation analysis (price vs averages)
    features.append("\n=== Deviation Analysis (Valuation) ===")
    features.append(f"Deviation_7d: {latest['Deviation_7d']:.2f}% (price vs 7d avg)")
    features.append(f"Deviation_30d: {latest['Deviation_30d']:.2f}% (price vs 30d avg)")
    features.append(f"Deviation_60d: {latest['Deviation_60d']:.2f}% (price vs 60d avg)")

    # Valuation status
    if latest['Deviation_30d'] > 20:
        valuation = "显著偏高"
    elif latest['Deviation_30d'] > 10:
        valuation = "偏高"
    elif latest['Deviation_30d'] < -20:
        valuation = "显著偏低"
    elif latest['Deviation_30d'] < -10:
        valuation = "偏低"
    else:
        valuation = "合理"
    features.append(f"Valuation Status: {valuation}")

    # Listings Trend (Supply Change)
    features.append("\n=== Listings Trend (Supply Change) ===")
    listings_trend = latest['Listings_Trend']
    features.append(f"Listings Change: {listings_trend:.2f}% (7d vs prev 7d)")
    if listings_trend > 20:
        supply_status = "供给大幅增加 (抛压风险)"
    elif listings_trend > 5:
        supply_status = "供给增加"
    elif listings_trend < -20:
        supply_status = "供给大幅减少 (稀缺溢价)"
    elif listings_trend < -5:
        supply_status = "供给减少"
    else:
        supply_status = "供给稳定"
    features.append(f"Supply Status: {supply_status}")

    # Listings & Volume (Supply & Activity)
    features.append("\n=== Listings & Volume (Supply & Activity) ===")
    listings = latest.get('listings', 0)
    volume = latest.get('volume', 0)
    features.append(f"Current Listings: {int(listings)}")
    features.append(f"24h Volume: {int(volume)}")
    vol_health = latest['Volume_Health']
    features.append(f"Volume/Listings Ratio: {vol_health:.4f}")

    # CS2 logic: high listings = good for buyers (easy to buy)
    # CS2 logic: low listings = bad for buyers (hard to buy)
    if listings > 500:
        liquidity = "充足 (买方容易买入)"
    elif listings > 100:
        liquidity = "一般"
    else:
        liquidity = "稀缺 (买方难以买入)"

    features.append(f"Supply Level: {liquidity}")

    # Volatility (Risk)
    features.append("\n=== Volatility (Risk) ===")
    vol_30d = latest['Volatility_30d']
    features.append(f"30d Volatility: {vol_30d:.2f}%")
    if vol_30d > 15:
        risk = "高风险"
    elif vol_30d > 8:
        risk = "中等风险"
    else:
        risk = "低风险"
    features.append(f"Risk Level: {risk}")

    # Long-term trend
    features.append("\n=== Long-term Trend ===")
    trend = "在MA60上方 (长期上涨)" if latest['low'] > latest['MA_60'] else "在MA60下方 (长期下跌)"
    features.append(f"MA60 Position: {trend}")

    # Summary
    features.append("\n=== Summary ===")
    signals = []

    # Valuation signals
    if latest['Deviation_30d'] > 20:
        signals.append("价格显著偏离30日均价")
    elif latest['Deviation_30d'] < -20:
        signals.append("价格显著低于30日均价")

    # Supply signals
    if latest['Listings_Trend'] < -20:
        signals.append("供给大幅减少")
    elif latest['Listings_Trend'] > 20:
        signals.append("供给大幅增加")

    # Supply signals (CS2: low listings = hard to buy)
    if listings < 100:
        signals.append("供给稀缺 (买方难以买入)")
    elif listings < 500 and latest['Listings_Trend'] < 0:
        signals.append("供给减少趋势")

    # Risk signals
    if latest['Volatility_30d'] > 15:
        signals.append("高波动风险")

    features.append(f"Key Signals: {', '.join(signals) if signals else '无明显信号'}")

    return "\n".join(features)


if __name__ == "__main__":
    # Test with mock data
    np.random.seed(42)

    # Generate mock CS2 market data (includes listings)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    close = 100 + np.cumsum(np.random.randn(100) * 2)

    df = pd.DataFrame({
        'date': dates,
        'open': close - np.random.rand(100) * 2,
        'low': close - np.random.rand(100) * 2,
        'listings': np.random.randint(100, 1000, 100),
        'volume': np.random.randint(10, 100, 100)
    })

    # Calculate indicators
    result = calculate_indicators(df)

    # Print DataFrame with CS2-specific columns
    print(result[['date', 'low', 'MA_7', 'MA_30', 'MA_60', 'Deviation_30d', 'Listings_Trend', 'Volume_Health', 'Volatility_30d']].tail(10))

    print("\n" + "="*50)
    print("Extracted Features:")
    print("="*50)
    print(extract_features(result))
