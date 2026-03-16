# CS2 Skin Quant Analyzer

[English](#english) | [中文](#中文)

---

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/zzzzhhzzz/cs2-quant-agent)](https://github.com/zzzzhhzzz/cs2-quant-agent/stargazers)

**CS2 (Counter-Strike 2) 饰品市场量化分析工具** - 自动获取 K 线数据、计算技术指标、生成 LLM 分析报告。

[Demo Report](#) · [Features](#features) · [Installation](#installation) · [Configuration](#configuration)

---

## English

### Features

- **K-line Data Scraping**: Fetch historical K-line data from SteamDT
- **CS2-Specific Indicators**:
  - Price deviation from MA (Deviation 7d/30d/60d)
  - Listings trend (supply change)
  - Volume health (liquidity ratio)
  - 30-day volatility
- **LLM Analysis Reports**: Generate professional reports via DeepSeek / OpenAI / Anthropic
- **Optional News Analysis**: Web search for latest CS2 news (disabled by default)

### Requirements

- Python 3.9+
- macOS / Linux / Windows

### Installation

```bash
git clone https://github.com/zzzzhhzzz/cs2-quant-agent.git
cd cs2_quant_agent
pip install -r requirements.txt
```

### Configuration

#### 1. Edit items.json

```json
{
  "news_enabled": false,
  "llm_provider": "deepseek",
  "items": [
    {
      "name": "USP-印花集",
      "url": "https://steamdt.com/cs2/USP-S%20%7C%20Printstream%20(Factory%20New)",
      "timeframe": "1h"
    }
  ]
}
```

#### 2. Set API Key (Optional)

| Provider | Environment Variable |
|----------|---------------------|
| DeepSeek | `DEEPSEEK_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

If not set, a mock client will be used.

#### 3. Enable News Analysis (Optional)

Set `news_enabled: true` in `items.json`.

### Run

```bash
python3 run.py
```

Reports → `output/` directory

### Indicators Reference

| Indicator | Description |
|-----------|-------------|
| Deviation_7d/30d/60d | Price deviation from 7/30/60-day MA |
| Listings_Trend | Listings change (7d vs previous 7d) |
| Volume_Health | Liquidity ratio (volume/listings) |
| Volatility_30d | 30-day price volatility |

### Important Notes

- Steam's **7-day trade cooldown** limits short-term strategies
- **Liquidity** (volume/listings) is the most critical risk indicator
- **High listings** = high supply = easy to buy (opposite to traditional markets)

---

## 中文

### 功能特性

- **K线数据爬取**: 从 SteamDT 获取历史 K 线数据
- **CS2 特有指标**:
  - 均线偏离度 (Deviation 7d/30d/60d)
  - 挂单量趋势 (供给变化)
  - 流动性比率
  - 30天波动率
- **LLM 分析报告**: 支持 DeepSeek / OpenAI / Anthropic
- **可选消息面分析**: 联网搜索 CS2 新闻 (默认关闭)

### 环境要求

- Python 3.9+
- macOS / Linux / Windows

### 安装

```bash
git clone https://github.com/zzzzhhzzz/cs2-quant-agent.git
cd cs2_quant_agent
pip install -r requirements.txt
```

### 配置

#### 1. 编辑 items.json

```json
{
  "news_enabled": false,
  "llm_provider": "deepseek",
  "items": [...]
}
```

#### 2. 设置 API Key

| 供应商 | 环境变量 |
|--------|---------|
| DeepSeek | `DEEPSEEK_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

#### 3. 开启消息面分析 (可选)

```json
"news_enabled": true
```

### 运行

```bash
python3 run.py
```

报告 → `output/` 目录

### 指标说明

| 指标 | 说明 |
|------|------|
| Deviation | 当前价相对均线的偏离度 |
| Listings_Trend | 挂单量变化 (7天 vs 前7天) |
| Volume_Health | 流动性比率 (成交量/挂单量) |
| Volatility_30d | 30天价格波动率 |

### 注意事项

- Steam **7天交易冷却** 限制短线策略
- **流动性** 是最重要的风险指标
- 挂单量大 = 供给充足 = 买方容易买入

---

## Links

- [GitHub](https://github.com/zzzzhhzzz/cs2-quant-agent)
- [SteamDT](https://steamdt.com)
- [Steam Market](https://steamcommunity.com/market/)

## License

MIT - See [LICENSE](LICENSE)
