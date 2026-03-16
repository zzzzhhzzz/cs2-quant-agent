# CS2 饰品量化分析工具

CS2 (Counter-Strike 2) 饰品市场量化分析工具，自动获取 K 线数据、计算技术指标、生成 LLM 分析报告。

## 功能特性

- **K线数据爬取**: 从 SteamDT 获取历史 K 线数据
- **CS2 特有指标**: 挂单量趋势、流动性比率、估值偏离度 (Deviation)、波动率等
- **LLM 分析报告**: 基于 DeepSeek API 生成专业分析报告
- **可选消息面分析**: 支持联网搜索 CS2 最新资讯 (默认关闭)

## 环境要求

- Python 3.9+
- macOS / Linux / Windows

## 安装

```bash
git clone https://github.com/zzzzhhzzz/cs2-quant-agent.git
cd cs2_quant_agent
pip install -r requirements.txt
```

## 配置

### 1. 编辑 items.json

```json
{
  "news_enabled": false,
  "items": [
    {
      "name": "USP-印花集",
      "url": "https://steamdt.com/cs2/USP-S%20%7C%20Printstream%20(Factory%20New)",
      "timeframe": "1h"
    },
    {
      "name": "AK-47-可燃冰",
      "url": "https://steamdt.com/cs2/AK-47%20%7C%20Ice%20Coaled%20(Factory%20New)",
      "timeframe": "1h"
    }
  ]
}
```

### 2. 设置 API Key (可选)

使用 LLM 分析需要 DeepSeek API Key：

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

如未设置 API Key，将使用 Mock 客户端生成简单报告。

### 3. 开启消息面分析 (可选)

将 `items.json` 中的 `news_enabled` 设为 `true` 即可联网搜索 CS2 新闻。

## 运行

```bash
python3 run.py
```

报告将保存在 `output/` 目录下。

## CS2 特有指标说明

| 指标 | 说明 |
|------|------|
| Deviation_7d/30d/60d | 当前价格相对均线的偏离度 |
| Listings_Trend | 挂单量变化趋势 (7天 vs 前7天) |
| Volume_Health | 流动性比率 (成交量/挂单量) |
| Volatility_30d | 30天价格波动率 |
| MA7/30/60 | 移动平均线 |

## 项目结构

```
cs2_quant_agent/
├── run.py                 # 主程序入口
├── items.json             # 配置文件
├── requirements.txt       # 依赖
├── src/
│   ├── data/              # 数据爬取模块
│   ├── features/          # 技术指标计算
│   ├── agent/             # LLM 客户端和提示词
│   └── automation/        # 自动化工具
└── output/                # 报告输出目录
```

## 注意事项

- Steam 7 天交易冷却限制了短线策略，必须使用持仓周期 > 7 天的波段策略
- 流动性 (成交量/挂单量) 是 CS2 市场最重要的风险指标
- 挂单量大 = 供给充足 = 买方容易买入 (与传统金融市场相反)

## License

MIT
