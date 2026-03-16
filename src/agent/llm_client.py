"""
LLM Client for CS2 Quantitative Analysis.
Supports Anthropic Claude and OpenAI GPT models.
"""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Try to import the LLM libraries
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .prompts import (
    SYSTEM_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    QUICK_ANALYSIS_PROMPT,
    COMPARISON_PROMPT
)


@dataclass
class MockMarketData:
    """Mock market data for testing."""
    item_name: str
    current_price: float
    avg_price_7d: float
    avg_price_30d: float
    volatility: float
    volume_24h: int
    price_change_7d: float
    price_change_30d: float
    holder_count: int
    market_depth: float
    whale_ratio: float
    new_addresses_7d: int
    tx_count_24h: int


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM."""
        pass


class AnthropicClient(LLMClient):
    """Anthropic Claude client."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text


class OpenAIClient(LLMClient):
    """OpenAI GPT client."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", base_url: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set OPENAI_API_KEY environment variable or pass api_key.")

        self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using GPT-4."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4096
        )
        return response.choices[0].message.content


class DeepSeekClient(LLMClient):
    """DeepSeek API client."""

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")

        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set DEEPSEEK_API_KEY environment variable or pass api_key.")

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using DeepSeek."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4096
        )
        return response.choices[0].message.content


class MockClient(LLMClient):
    """Mock client for testing without API calls."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return a formatted mock response based on the input data."""
        # Detect prompt type and generate appropriate response
        if "快速分析" in user_prompt or "Quick Analysis" in user_prompt or "3-4 句话" in user_prompt:
            return self._generate_quick_analysis(user_prompt)
        elif "对比分析" in user_prompt or "对比品种" in user_prompt:
            return self._generate_comparison(user_prompt)
        else:
            return self._generate_full_analysis(user_prompt)

    def _extract_item_name(self, user_prompt: str) -> str:
        """Extract item name from prompt."""
        # Try "item_name:" format first
        if "item_name:" in user_prompt:
            try:
                start = user_prompt.index("item_name:") + len("item_name:")
                end = user_prompt.index("\n", start)
                return user_prompt[start:end].strip()
            except ValueError:
                pass
        # Try "对 {item_name} 进行快速分析" format
        if "对 " in user_prompt and " 进行快速分析" in user_prompt:
            try:
                start = user_prompt.index("对 ") + len("对 ")
                end = user_prompt.index(" 进行快速分析")
                return user_prompt[start:end].strip()
            except ValueError:
                pass
        return "AK-47 | Redline"

    def _extract_value(self, user_prompt: str, key: str) -> str:
        """Extract a value from the prompt."""
        if key + ":" in user_prompt:
            try:
                start = user_prompt.index(key + ":") + len(key + ":")
                # Try to find end at newline, " USD", "%", or end of prompt
                remaining = user_prompt[start:]
                for end_marker in ["\n", " USD", "%", " "]:
                    if end_marker in remaining:
                        end = start + remaining.index(end_marker)
                        return user_prompt[start:end].strip()
                # If no end marker found, take until end of prompt
                return remaining.strip()
            except ValueError:
                pass
        return "N/A"

    def _generate_quick_analysis(self, user_prompt: str) -> str:
        """Generate a quick analysis response."""
        item_name = self._extract_item_name(user_prompt)
        current_price = self._extract_value(user_prompt, "current_price")
        price_change = self._extract_value(user_prompt, "price_change_7d")

        return f"""**{item_name}** 快速分析：

当前价格 ${current_price}，近7日变化 {price_change}%。短期走势偏多，建议逢低布局，止损设置在-5%位置。风险等级中等，适合区间操作。"""

    def _generate_comparison(self, user_prompt: str) -> str:
        """Generate a comparison analysis response."""
        return f"""# CS2 市场对比分析报告

## 一、整体市场概述
当前市场处于分化状态，高端饰品表现较弱，中端饰品走势稳健。

## 二、品种对比分析

### AK-47 | Redline
- 当前价格: $15.67
- 7日变化: +2.89%
- 波动率: 8.5%
- 评价: ★★★★☆ 推荐买入

### AWP | Asiimov
- 当前价格: $52.34
- 7日变化: +0.87%
- 波动率: 6.2%
- 评价: ★★★★☆ 持有观望

### Karambit | Fade
- 当前价格: $892.50
- 7日变化: +1.96%
- 波动率: 12.3%
- 评价: ★★★☆☆ 高波动风险

### M4A4 | Howl
- 当前价格: $1850.00
- 7日变化: -3.67%
- 波动率: 15.7%
- 评价: ★★☆☆☆ 建议回避

## 三、推荐排序
1. AK-47 | Redline - 性价比高，流动性好
2. AWP | Asiimov - 稳健增值
3. Karambit | Fade - 高风险高回报
4. M4A4 | Howl - 价格承压

## 四、风险提示
- 市场波动加剧，建议控制仓位
- 高价值饰品流动性较低
- 注意设置止损位

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""

    def _generate_full_analysis(self, user_prompt: str) -> str:
        """Generate a full analysis report."""
        item_name = self._extract_item_name(user_prompt)
        return f"""# {item_name} 市场分析报告

## 一、市场概况
当前 {item_name} 处于**震荡上行**状态。短期价格获得支撑，市场活跃度较高。

## 二、价格分析

### 2.1 短期走势
近7日价格呈现小幅上涨趋势，市场买盘意愿较强，预计短期仍有上行动能。

### 2.2 中期趋势
近30日价格走势平稳，波动率处于合理区间，市场情绪偏向乐观。

## 三、供需关系

### 3.1 持仓分布
大户持仓比例适中，筹码分布较为分散，有利于行情健康发展。

### 3.2 交易活跃度
24小时转账次数活跃，市场流动性良好，买卖盘深度充足。

## 四、技术指标

### 4.1 波动率分析
价格波动率处于中等水平，既不过于剧烈也不过于平淡，适合区间操作。

### 4.2 市场深度
市场深度良好，大单成交对价格影响有限，流动性风险较低。

## 五、投资建议

### 5.1 趋势判断
**震荡上行** - 短期偏多，中期维持看涨

### 5.2 风险评估
**中等风险** - 建议设置止损位，控制仓位

### 5.3 操作建议
- **买入建议**: 逢低布局，支撑位附近建仓
- **卖出建议**: 达到预期收益后可分批止盈
- **观望**: 风险偏好较低者可等待突破确认

---
*本报告基于市场数据分析，仅供参考，不构成投资建议*
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""


class CS2Analyzer:
    """
    CS2 Market Analysis Agent.
    Supports Claude, OpenAI, and Mock clients.
    """

    def __init__(
        self,
        provider: str = "mock",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the CS2 analyzer.

        Args:
            provider: LLM provider - "anthropic", "openai", or "mock"
            api_key: API key for the provider
            model: Model name (optional, uses defaults)
        """
        self.provider = provider.lower()
        self.client = self._create_client(api_key, model)

    def _create_client(self, api_key: Optional[str], model: Optional[str]) -> LLMClient:
        """Create the appropriate LLM client."""
        if self.provider == "anthropic":
            return AnthropicClient(api_key, model or "claude-3-5-sonnet-20241022")
        elif self.provider == "openai":
            return OpenAIClient(api_key, model or "gpt-4o")
        elif self.provider == "deepseek":
            return DeepSeekClient(api_key, model or "deepseek-chat")
        elif self.provider == "mock":
            return MockClient()
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'anthropic', 'openai', 'deepseek', or 'mock'")

    def analyze(
        self,
        item_name: str,
        current_price: float,
        avg_price_7d: float,
        avg_price_30d: float,
        volatility: float,
        volume_24h: int,
        price_change_7d: float,
        price_change_30d: float,
        holder_count: int,
        market_depth: float,
        whale_ratio: float,
        new_addresses_7d: int,
        tx_count_24h: int
    ) -> str:
        """
        Generate a comprehensive market analysis report.

        Args:
            item_name: Name of the item
            current_price: Current price in USD
            avg_price_7d: 7-day average price
            avg_price_30d: 30-day average price
            volatility: Price volatility (%)
            volume_24h: 24-hour trading volume
            price_change_7d: 7-day price change (%)
            price_change_30d: 30-day price change (%)
            holder_count: Number of holders
            market_depth: Market depth score
            whale_ratio: Whale holding ratio (%)
            new_addresses_7d: New addresses in 7 days
            tx_count_24h: 24-hour transaction count

        Returns:
            Formatted Markdown analysis report
        """
        user_prompt = MARKET_ANALYSIS_PROMPT.format(
            item_name=item_name,
            current_price=current_price,
            avg_price_7d=avg_price_7d,
            avg_price_30d=avg_price_30d,
            volatility=volatility,
            volume_24h=volume_24h,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            holder_count=holder_count,
            market_depth=market_depth,
            whale_ratio=whale_ratio,
            new_addresses_7d=new_addresses_7d,
            tx_count_24h=tx_count_24h,
            report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        return self.client.generate(SYSTEM_PROMPT, user_prompt)

    def quick_analyze(self, item_name: str, current_price: float, price_change_7d: float) -> str:
        """
        Generate a quick analysis with minimal data.

        Args:
            item_name: Name of the item
            current_price: Current price in USD
            price_change_7d: 7-day price change (%)

        Returns:
            Short analysis summary
        """
        user_prompt = QUICK_ANALYSIS_PROMPT.format(
            item_name=item_name,
            current_price=current_price,
            price_change_7d=price_change_7d
        )

        return self.client.generate(SYSTEM_PROMPT, user_prompt)

    def compare_items(self, items_data: List[Dict[str, Any]]) -> str:
        """
        Generate a comparison analysis for multiple items.

        Args:
            items_data: List of item data dictionaries

        Returns:
            Formatted comparison report
        """
        items_list = "\n".join([f"- {item['item_name']}" for item in items_data])
        data_summary = "\n\n".join([
            f"### {item['item_name']}\n- 价格: ${item['current_price']}\n- 7日变化: {item['price_change_7d']}%\n- 波动率: {item['volatility']}%"
            for item in items_data
        ])

        user_prompt = COMPARISON_PROMPT.format(
            items_list=items_list,
            data_summary=data_summary
        )

        return self.client.generate(SYSTEM_PROMPT, user_prompt)

    @staticmethod
    def get_mock_data() -> MockMarketData:
        """
        Get sample mock market data for testing.

        Returns:
            MockMarketData instance with sample data
        """
        return MockMarketData(
            item_name="AK-47 | Redline (Field-Tested)",
            current_price=15.67,
            avg_price_7d=15.23,
            avg_price_30d=14.89,
            volatility=8.5,
            volume_24h=125000,
            price_change_7d=2.89,
            price_change_30d=5.23,
            holder_count=45230,
            market_depth=0.75,
            whale_ratio=23.5,
            new_addresses_7d=1250,
            tx_count_24h=8920
        )

    @staticmethod
    def get_mock_data_collection() -> List[MockMarketData]:
        """
        Get a collection of mock market data for multiple items.

        Returns:
            List of MockMarketData instances
        """
        return [
            MockMarketData(
                item_name="AK-47 | Redline (Field-Tested)",
                current_price=15.67,
                avg_price_7d=15.23,
                avg_price_30d=14.89,
                volatility=8.5,
                volume_24h=125000,
                price_change_7d=2.89,
                price_change_30d=5.23,
                holder_count=45230,
                market_depth=0.75,
                whale_ratio=23.5,
                new_addresses_7d=1250,
                tx_count_24h=8920
            ),
            MockMarketData(
                item_name="AWP | Asiimov (Battle-Scarred)",
                current_price=52.34,
                avg_price_7d=51.89,
                avg_price_30d=50.12,
                volatility=6.2,
                volume_24h=89000,
                price_change_7d=0.87,
                price_change_30d=4.23,
                holder_count=32100,
                market_depth=0.68,
                whale_ratio=18.2,
                new_addresses_7d=890,
                tx_count_24h=5430
            ),
            MockMarketData(
                item_name="Karambit | Fade (Factory New)",
                current_price=892.50,
                avg_price_7d=875.30,
                avg_price_30d=850.00,
                volatility=12.3,
                volume_24h=15000,
                price_change_7d=1.96,
                price_change_30d=5.0,
                holder_count=5680,
                market_depth=0.45,
                whale_ratio=35.8,
                new_addresses_7d=120,
                tx_count_24h=890
            ),
            MockMarketData(
                item_name="M4A4 | Howl (Field-Tested)",
                current_price=1850.00,
                avg_price_7d=1920.50,
                avg_price_30d=2050.00,
                volatility=15.7,
                volume_24h=5200,
                price_change_7d=-3.67,
                price_change_30d=-9.76,
                holder_count=8920,
                market_depth=0.32,
                whale_ratio=42.1,
                new_addresses_7d=45,
                tx_count_24h=320
            )
        ]


def main():
    """Demo function to test the analyzer."""
    print("=" * 60)
    print("CS2 量化分析工具 - 测试演示")
    print("=" * 60)

    # Use mock client for testing
    analyzer = CS2Analyzer(provider="mock")

    # Get mock data
    mock_data = analyzer.get_mock_data()

    print("\n[1] 单品种详细分析")
    print("-" * 40)

    report = analyzer.analyze(
        item_name=mock_data.item_name,
        current_price=mock_data.current_price,
        avg_price_7d=mock_data.avg_price_7d,
        avg_price_30d=mock_data.avg_price_30d,
        volatility=mock_data.volatility,
        volume_24h=mock_data.volume_24h,
        price_change_7d=mock_data.price_change_7d,
        price_change_30d=mock_data.price_change_30d,
        holder_count=mock_data.holder_count,
        market_depth=mock_data.market_depth,
        whale_ratio=mock_data.whale_ratio,
        new_addresses_7d=mock_data.new_addresses_7d,
        tx_count_24h=mock_data.tx_count_24h
    )

    print(report)

    print("\n[2] 快速分析")
    print("-" * 40)

    quick_report = analyzer.quick_analyze(
        item_name="AWP | Asiimov",
        current_price=52.34,
        price_change_7d=0.87
    )
    print(quick_report)

    print("\n[3] 多品种对比分析")
    print("-" * 40)

    mock_collection = analyzer.get_mock_data_collection()
    items_data = [
        {
            "item_name": item.item_name,
            "current_price": item.current_price,
            "price_change_7d": item.price_change_7d,
            "volatility": item.volatility
        }
        for item in mock_collection
    ]

    comparison_report = analyzer.compare_items(items_data)
    print(comparison_report)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
