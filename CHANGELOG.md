# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-03-16

### Added
- K-line data scraping from SteamDT
- CS2-specific technical indicators (MA, Deviation, Listings Trend, Volume Health, Volatility)
- LLM analysis reports via DeepSeek/OpenAI/Anthropic API
- Optional news analysis via web search
- Bilingual README (English/Chinese)
- Multi-LLM provider support

### Features
- `news_enabled` config to toggle news fetching
- `llm_provider` config to switch between anthropic/openai/deepseek/mock
- Configurable items in items.json

### Technical Indicators
- MA7, MA30, MA60 (Moving Averages)
- Deviation_7d/30d/60d (Price deviation from MA)
- Listings_Trend (Supply change)
- Volume_Health (Liquidity ratio)
- Volatility_30d (Price volatility)

## [0.x] - Pre-release

### Initial Development
- K-line scraper implementation
- Indicator calculation module
- LLM client integration
- Basic report generation
