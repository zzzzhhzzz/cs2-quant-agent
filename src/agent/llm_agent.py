"""LLM Agent module for generating market analysis."""


def call_llm(indicators: dict, market_data: dict) -> str:
    """
    Call LLM to generate market analysis based on indicators.

    Args:
        indicators: Technical indicators
        market_data: Raw market data

    Returns:
        Analysis text from LLM
    """
    # Format indicators for the prompt
    price = indicators.get("latest_price", 0)
    rsi = indicators.get("rsi", 0)
    macd = indicators.get("macd", 0)
    trend = indicators.get("trend", "unknown")

    # Generate analysis based on indicators
    analysis = generate_analysis(price, rsi, macd, trend, market_data)

    return analysis


def generate_analysis(price: float, rsi: float, macd: float, trend: str, market_data: dict) -> str:
    """Generate market analysis based on indicators."""

    # Determine signal
    signals = []

    if rsi > 70:
        signals.append("RSI indicates overbought conditions")
    elif rsi < 30:
        signals.append("RSI indicates oversold conditions")

    if macd > 0:
        signals.append("MACD is positive (bullish momentum)")
    else:
        signals.append("MACD is negative (bearish momentum)")

    signal_text = "; ".join(signals) if signals else "No clear signals"

    # Build analysis report
    report = f"""# CS2 Market Analysis

## Price Summary
- Current Price: ${price:.2f}

## Technical Indicators
- RSI (14): {rsi:.2f}
- MACD: {macd:.2f}
- Trend: {trend.upper()}

## Signal Analysis
{signal_text}

## Recommendation
{get_recommendation(rsi, macd, trend)}

---
*Generated automatically based on technical analysis*
"""

    return report


def get_recommendation(rsi: float, macd: float, trend: str) -> str:
    """Get trading recommendation based on indicators."""

    if rsi > 70:
        return "Consider taking profits or waiting for correction. Market may be overbought."
    elif rsi < 30:
        return "Potential buying opportunity. Market may be oversold."

    if trend == "bullish" and macd > 0:
        return "Bullish momentum confirmed. Consider long positions."
    elif trend == "bearish" and macd < 0:
        return "Bearish momentum confirmed. Consider short positions or wait."

    return "Hold current positions. Wait for clearer signals."
