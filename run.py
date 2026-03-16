#!/usr/bin/env python3
"""
CS2 K-Line Monitor - Configuration-driven scraper.
Reads items.json and generates analysis reports for each item.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.kline_scraper import scrape_kline
from src.data.news_fetcher import fetch_item_related_news, format_news_for_prompt
from src.features.indicators import calculate_indicators, extract_features
from src.agent.llm_client import MockClient, CS2Analyzer


def load_config(config_path: str = "items.json") -> dict:
    """Load items configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_analysis(item_name: str, features_text: str, df, news_enabled: bool = False) -> str:
    """
    Generate analysis report using LLM with CS2-specific indicators.

    Args:
        item_name: Name of the item
        features_text: Extracted CS2-specific features
        df: DataFrame with K-line data and CS2 indicators
        news_enabled: Whether to fetch news (default: False)

    Returns:
        Analysis report string
    """
    # In CS2 market, "low" (floor price) is the most important
    # Use "low" as the primary price instead of "close"
    price_col = 'low'

    # Derive market data from K-line
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    current_price = latest[price_col]

    # CS2-specific metrics from indicators
    deviation_7d = latest.get('Deviation_7d', 0)
    deviation_30d = latest.get('Deviation_30d', 0)
    deviation_60d = latest.get('Deviation_60d', 0)
    listings_trend = latest.get('Listings_Trend', 0)
    volume_health = latest.get('Volume_Health', 0)
    volatility_30d = latest.get('Volatility_30d', 0)

    # Volume metrics
    volume_24h = int(latest['volume']) if 'volume' in latest else 0

    # Listings metrics
    listings = int(latest['listings']) if 'listings' in latest else 0

    # MA values
    ma_30 = latest.get('MA_30', 0)
    ma_60 = latest.get('MA_60', 0)

    # Time-based price changes
    from datetime import timedelta
    latest_time = latest['date']

    # 7 days ago
    time_7d_ago = latest_time - timedelta(days=7)
    df_7d = df[df['date'] >= time_7d_ago]

    # 30 days ago
    time_30d_ago = latest_time - timedelta(days=30)
    df_30d = df[df['date'] >= time_30d_ago]

    # 7-day change
    if len(df_7d) >= 2:
        price_change_7d = ((df_7d[price_col].iloc[-1] / df_7d[price_col].iloc[0]) - 1) * 100
    else:
        price_change_7d = 0

    # 30-day change
    if len(df_30d) >= 2:
        price_change_30d = ((df_30d[price_col].iloc[-1] / df_30d[price_col].iloc[0]) - 1) * 100
    else:
        price_change_30d = 0

    # Build a custom analysis with item name baked in
    # Use DeepSeek client with API key
    DEEPSEEK_API_KEY = "sk-c413519571d048a6b29d1a34f481f100"
    analyzer = CS2Analyzer(provider="deepseek", api_key=DEEPSEEK_API_KEY)

    # Prepare K-line data for LLM (last 30 periods with CS2 indicators)
    recent_klines = df.tail(30).copy()

    # Format K-line data as text (CS2-specific indicators)
    kline_data = []
    kline_data.append("时间,开盘价,底价,挂单量,成交量,MA7,MA30,MA60,偏差7d%,偏差30d%,偏差60d%,挂单趋势%,流动性,波动率%")
    for _, row in recent_klines.iterrows():
        # Format date
        date_val = row['date']
        if hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = str(date_val)

        # Helper to format values
        def fmt(val, fmt_str='.2f'):
            if pd.isna(val):
                return 'N/A'
            try:
                return f"{val:{fmt_str}}"
            except:
                return str(val)

        line = f"{date_str}," \
               f"{fmt(row['open'])},{fmt(row['low'])}," \
               f"{int(row['listings']) if pd.notna(row['listings']) and row['listings'] else 0}," \
               f"{int(row['volume']) if pd.notna(row['volume']) and row['volume'] else 0}," \
               f"{fmt(row.get('MA_7', 'N/A'))},{fmt(row.get('MA_30', 'N/A'))},{fmt(row.get('MA_60', 'N/A'))}," \
               f"{fmt(row.get('Deviation_7d', 'N/A'))},{fmt(row.get('Deviation_30d', 'N/A'))},{fmt(row.get('Deviation_60d', 'N/A'))}," \
               f"{fmt(row.get('Listings_Trend', 'N/A'))},{fmt(row.get('Volume_Health', 'N/A'))},{fmt(row.get('Volatility_30d', 'N/A'))}"
        kline_data.append(line)

    kline_text = "\n".join(kline_data)

    # 获取消息面数据（可选）
    if news_enabled:
        print(f"[NEWS] Fetching news for: {item_name}")
        try:
            news_list = fetch_item_related_news(item_name, max_items=8)
            news_text = format_news_for_prompt(news_list)
            print(f"[NEWS] Got {len(news_list)} news items")
        except Exception as e:
            print(f"[WARN] Failed to fetch news: {e}")
            news_text = "获取消息失败，跳过基本面分析"
    else:
        news_text = "*(消息面分析已关闭)*"

    custom_prompt = f"""请分析以下CS2饰品的CS2特有指标数据：

## 饰品信息
- 名称: {item_name}
- 当前价格: ¥{current_price:.2f}
- 挂单量: {listings}
- 24小时成交量: {volume_24h}
- 7日涨跌: {price_change_7d:.2f}%
- 30日涨跌: {price_change_30d:.2f}%

## CS2 特有指标（重点分析）
- MA30: ¥{ma_30:.2f}
- MA60: ¥{ma_60:.2f}
- 偏差(7天): {deviation_7d:.2f}% (当前价/MA7 -1)
- 偏差(30天): {deviation_30d:.2f}% (当前价/MA30 -1)
- 偏差(60天): {deviation_60d:.2f}% (当前价/MA60 -1)
- 挂单趋势: {listings_trend:.2f}% (近7天vs前7天挂单量变化)
- 流动性比率: {volume_health:.4f} (成交量均值/挂单量均值)
- 30天波动率: {volatility_30d:.2f}%

## 最近30期K线数据（CS2特有指标）
{kline_text}

{news_text}

请基于以上CS2特有指标数据进行深入分析，包括：
1. 估值合理性：当前价格 vs 30天/60天均价，判断价格是否偏高或偏低
2. 流动性健康度：成交量/挂单量比值，评估买卖流动性风险
3. 供给变化：挂单量趋势，判断供给增加还是减少
4. 长线趋势：价格在 MA60 上方还是下方
5. 波动率风险：30天波动率评估
6. 综合投资建议

**重要：禁止使用传统金融指标分析（如 MACD、RSI、布林带），必须使用上述 CS2 特有指标。**

请生成一份专业的 CS2 饰品量化分析报告。"""

    from src.agent.llm_client import SYSTEM_PROMPT
    report = analyzer.client.generate(SYSTEM_PROMPT, custom_prompt)

    # Append CS2 indicators section
    report += f"\n\n---\n\n## CS2 特有指标分析\n\n{features_text}"

    return report


def save_report(item_name: str, report: str, output_dir: str = "output") -> str:
    """Save analysis report to file."""
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize item name for filename
    safe_name = item_name.replace("/", "-").replace(" ", "_")
    filename = f"{safe_name}_{timestamp}.md"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)

    return filepath


def save_kline(item_name: str, df, output_dir: str = "output") -> str:
    """Save K-line data to CSV file (only essential columns)."""
    import pandas as pd
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = item_name.replace("/", "-").replace(" ", "_")
    filename = f"{safe_name}_kline_{timestamp}.csv"

    # Keep only essential columns: timestamp, date, open, listings, low, volume
    # In CS2 market, "low" (floor price) is the most important
    essential_cols = ['timestamp', 'date', 'open', 'listings', 'low', 'volume']
    df_essential = df[[c for c in essential_cols if c in df.columns]]

    filepath = os.path.join(output_dir, filename)
    df_essential.to_csv(filepath, index=False, encoding='utf-8-sig')

    return filepath


def process_item(item: dict, news_enabled: bool = False) -> dict:
    """
    Process a single item: scrape K-line, calculate indicators, generate report.

    Args:
        item: Dict with 'name', 'url', 'timeframe' keys
        news_enabled: Whether to fetch news

    Returns:
        Dict with processing result
    """
    name = item['name']
    url = item['url']
    timeframe = item.get('timeframe', '1h')

    print(f"\n{'='*60}")
    print(f"Processing: {name}")
    print(f"URL: {url}")
    print(f"Timeframe: {timeframe}")
    print(f"{'='*60}")

    try:
        # Step 1: Scrape K-line data
        print(f"[1/4] Scraping K-line data...")
        df = scrape_kline(url, timeframe)

        if df is None or df.empty:
            print(f"[ERROR] No K-line data retrieved for {name}")
            return {
                "item": name,
                "success": False,
                "error": "No K-line data retrieved"
            }

        print(f"  Retrieved {len(df)} rows of K-line data")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

        # Save K-line data to CSV
        kline_path = save_kline(name, df)
        print(f"  K-line data saved to: {kline_path}")

        # Step 2: Calculate technical indicators
        print(f"[2/4] Calculating technical indicators...")
        df_with_indicators = calculate_indicators(df)
        features_text = extract_features(df_with_indicators)

        # Step 3: Generate analysis report
        print(f"[3/4] Generating analysis report...")
        report = generate_analysis(name, features_text, df_with_indicators, news_enabled)

        # Step 4: Save report
        print(f"[4/4] Saving report...")
        output_path = save_report(name, report)
        print(f"  Report saved to: {output_path}")

        return {
            "item": name,
            "success": True,
            "output_path": output_path,
            "data_rows": len(df)
        }

    except Exception as e:
        print(f"[ERROR] Failed to process {name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "item": name,
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point."""
    print("=" * 60)
    print("CS2 K-Line Monitor")
    print("Configuration-driven K-line scraper")
    print("=" * 60)

    # Load configuration
    config_path = project_root / "items.json"

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("Please create items.json in the project root.")
        sys.exit(1)

    print(f"\nLoading configuration from: {config_path}")
    config = load_config(str(config_path))

    items = config.get('items', [])
    print(f"Found {len(items)} items to process")

    if not items:
        print("No items found in configuration.")
        sys.exit(1)

    # Get news config
    news_enabled = config.get('news_enabled', False)
    if news_enabled:
        print("\n[NEWS] News fetching is ENABLED")
    else:
        print("\n[NEWS] News fetching is DISABLED (set news_enabled: true in items.json to enable)")

    # Process each item
    results = []
    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] Processing item...")
        result = process_item(item, news_enabled=news_enabled)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count

    print(f"Total items: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

    if fail_count > 0:
        print("\nFailed items:")
        for r in results:
            if not r['success']:
                print(f"  - {r['item']}: {r.get('error', 'Unknown error')}")

    print("\nDone!")


if __name__ == "__main__":
    main()
