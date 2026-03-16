# CS2 饰品量化分析工具 / CS2 Skin Quant Analyzer

[English](#english) | [中文](#中文)

---

## English

CS2 (Counter-Strike 2) skin market quantitative analysis tool. Automatically fetches K-line data, calculates technical indicators, and generates LLM-powered analysis reports.

### Features

- **K-line Data Scraping**: Fetch historical K-line data from SteamDT
- **CS2-Specific Indicators**: Listings trend, liquidity ratio, price deviation, volatility, etc.
- **LLM Analysis Reports**: Generate professional reports via DeepSeek API
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

DeepSeek API Key is required for LLM analysis:

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

If not set, a mock client will be used to generate simple reports.

#### 3. Enable News Analysis (Optional)

Set `news_enabled: true` in `items.json` to enable web search for CS2 news.

### Run

```bash
python3 run.py
```

Reports will be saved in the `output/` directory.

### CS2-Specific Indicators

| Indicator | Description |
|-----------|-------------|
| Deviation_7d/30d/60d | Price deviation from moving average |
| Listings_Trend | Listings change (7d vs previous 7d) |
| Volume_Health | Liquidity ratio (volume/listings) |
| Volatility_30d | 30-day price volatility |
| MA7/30/60 | Moving averages |

### Important Notes

- Steam's 7-day trade cooldown limits short-term strategies; positions must be held > 7 days
- Liquidity (volume/listings) is the most important risk indicator
- High listings = high supply = easy to buy (opposite to traditional financial markets)

---

## 中文

CS2 (Counter-Strike 2) 饰品市场量化分析工具，自动获取 K 线数据、计算技术指标、生成 LLM 分析报告。

### 功能特性

- **K线数据爬取**: 从 SteamDT 获取历史 K 线数据
- **CS2 特有指标**: 挂单量趋势、流动性比率、估值偏离度 (Deviation)、波动率等
- **LLM 分析报告**: 基于 DeepSeek API 生成专业分析报告
- **可选消息面分析**: 支持联网搜索 CS2 最新资讯 (默认关闭)

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
  "items": [
    {
      "name": "USP-印花集",
      "url": "https://steamdt.com/cs2/USP-S%20%7C%20Printstream%20(Factory%20New)",
      "timeframe": "1h"
    }
  ]
}
```

#### 2. 设置 API Key (可选)

使用 LLM 分析需要 DeepSeek API Key：

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

如未设置 API Key，将使用 Mock 客户端生成简单报告。

#### 3. 开启消息面分析 (可选)

将 `items.json` 中的 `news_enabled` 设为 `true` 即可联网搜索 CS2 新闻。

### 运行

```bash
python3 run.py
```

报告将保存在 `output/` 目录下。

### CS2 特有指标说明

| 指标 | 说明 |
|------|------|
| Deviation_7d/30d/60d | 当前价格相对均线的偏离度 |
| Listings_Trend | 挂单量变化趋势 (7天 vs 前7天) |
| Volume_Health | 流动性比率 (成交量/挂单量) |
| Volatility_30d | 30天价格波动率 |
| MA7/30/60 | 移动平均线 |

### 注意事项

- Steam 7 天交易冷却限制了短线策略，必须使用持仓周期 > 7 天的波段策略
- 流动性 (成交量/挂单量) 是 CS2 市场最重要的风险指标
- 挂单量大 = 供给充足 = 买方容易买入 (与传统金融市场相反)

---

## License

MIT
