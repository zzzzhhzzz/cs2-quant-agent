"""CS2 Quant Agent - AI Research Brain."""

from .llm_client import CS2Analyzer, MockMarketData
from .prompts import (
    SYSTEM_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    QUICK_ANALYSIS_PROMPT,
    COMPARISON_PROMPT
)

__all__ = [
    "CS2Analyzer",
    "MockMarketData",
    "SYSTEM_PROMPT",
    "MARKET_ANALYSIS_PROMPT",
    "QUICK_ANALYSIS_PROMPT",
    "COMPARISON_PROMPT"
]
