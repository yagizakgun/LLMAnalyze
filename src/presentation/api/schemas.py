"""Pydantic response schemas for the API layer."""

from pydantic import BaseModel, Field, model_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime


def _round_floats(obj: Any, precision: int = 2) -> Any:
    """Recursively round all float values in a nested structure."""
    if isinstance(obj, float):
        return round(obj, precision)
    elif isinstance(obj, dict):
        return {k: _round_floats(v, precision) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_round_floats(item, precision) for item in obj]
    return obj


class TechnicalIndicatorsResponse(BaseModel):
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr_14: Optional[float] = None


class SignalResponse(BaseModel):
    symbol: str
    type: str
    strength: float = Field(ge=0.0, le=1.0)
    reason: str
    timestamp: Optional[datetime] = None
    source: str = "SYSTEM"


class NewsArticleResponse(BaseModel):
    title: str
    url: str
    published_at: Optional[datetime] = None
    source: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None
    category: Optional[str] = None
    keywords: List[str] = []
    image_url: Optional[str] = None
    content: Optional[str] = None


class TrendingTopicResponse(BaseModel):
    topic: str
    mention_count: int
    sentiment: str
    related_symbols: List[str] = []


class NewsImpactResponse(BaseModel):
    impact_score: float
    price_impact_prediction: str
    confidence: float
    reasoning: str
    affected_sectors: List[str] = []


class NewsSummaryResponse(BaseModel):
    timestamp: datetime
    market_status: str
    key_events: List[str]
    overall_sentiment: str
    trending_topics: List[TrendingTopicResponse]


class SentimentResponse(BaseModel):
    overall_sentiment: str
    score: float = Field(ge=-1.0, le=1.0)
    key_themes: List[str] = []
    bullish_factors: List[str] = []
    bearish_factors: List[str] = []


class LLMAnalysisResponse(BaseModel):
    summary: str
    signal: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_levels: Dict[str, float] = {}
    provider: str = "Unknown"


class AnalysisResponse(BaseModel):
    """Full analysis response returned by the API."""

    symbol: str
    timeframe: str
    current_price: float
    timestamp: Optional[datetime] = None
    technical_indicators: Optional[TechnicalIndicatorsResponse] = None
    technical_signal: Optional[SignalResponse] = None
    news: List[NewsArticleResponse] = []
    news_sentiment: Optional[SentimentResponse] = None
    llm_analysis: Optional[LLMAnalysisResponse] = None
    final_signal: Optional[SignalResponse] = None
    contradictions: List[str] = []

    model_config = {"from_attributes": True}

    @model_serializer(mode="wrap")
    def _round_all_floats(self, handler):
        data = handler(self)
        return _round_floats(data)


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_type: str = "unknown"
