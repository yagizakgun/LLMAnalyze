from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .enums import SignalType, TimeFrame, Sentiment, AlertType, NewsCategory

@dataclass
class StockInfo:
    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None

@dataclass
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class TechnicalIndicators:
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
    
    @property
    def is_oversold_rsi(self) -> bool:
        return self.rsi_14 is not None and self.rsi_14 < 30
    
    @property
    def is_overbought_rsi(self) -> bool:
        return self.rsi_14 is not None and self.rsi_14 > 70

@dataclass
class Signal:
    symbol: str
    type: SignalType
    strength: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "SYSTEM"  # e.g., "TECHNICAL", "LLM", "SENTIMENT"

@dataclass
class NewsArticle:
    title: str
    url: str
    published_at: datetime
    source: str
    summary: Optional[str] = None
    sentiment: Optional[Sentiment] = None
    sentiment_score: Optional[float] = None # -1.0 to 1.0
    # New fields for advanced news
    relevance_score: Optional[float] = None # 0.0 to 1.0
    category: Optional[NewsCategory] = None
    keywords: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    content: Optional[str] = None

@dataclass
class TrendingTopic:
    topic: str
    mention_count: int
    sentiment: Sentiment
    related_symbols: List[str] = field(default_factory=list)

@dataclass
class NewsImpactAnalysis:
    impact_score: float # -1.0 (very negative) to 1.0 (very positive)
    price_impact_prediction: str # Short description e.g., "Short-term downside risk"
    confidence: float # 0.0 to 1.0
    reasoning: str
    affected_sectors: List[str] = field(default_factory=list)

@dataclass
class NewsSummary:
    timestamp: datetime
    market_status: str
    key_events: List[str]
    overall_sentiment: Sentiment
    trending_topics: List[TrendingTopic]


@dataclass
class SentimentResult:
    overall_sentiment: Sentiment
    score: float # -1.0 to 1.0
    key_themes: List[str]
    bullish_factors: List[str]
    bearish_factors: List[str]

@dataclass
class LLMAnalysisResult:
    summary: str
    signal: SignalType
    confidence: float # 0.0 to 1.0
    reasoning: str
    key_levels: Dict[str, float] = field(default_factory=dict) # e.g., {"support_1": 150.0, "resistance_1": 160.0}
    provider: str = "Unknown"

@dataclass
class AnalysisResult:
    symbol: str
    timeframe: TimeFrame
    current_price: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    technical_indicators: Optional[TechnicalIndicators] = None
    technical_signal: Optional[Signal] = None
    news: List[NewsArticle] = field(default_factory=list)
    news_sentiment: Optional[SentimentResult] = None
    llm_analysis: Optional[LLMAnalysisResult] = None
    final_signal: Optional[Signal] = None
    contradictions: List[str] = field(default_factory=list)

@dataclass
class PortfolioPosition:
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    
    @property
    def market_value(self) -> Optional[float]:
        if self.current_price is None: return None
        return self.quantity * self.current_price
        
    @property
    def unrealized_pnl(self) -> Optional[float]:
        if self.current_price is None: return None
        return (self.current_price - self.average_price) * self.quantity
        
    @property
    def unrealized_pnl_percent(self) -> Optional[float]:
        if self.current_price is None or self.average_price == 0: return None
        return ((self.current_price - self.average_price) / self.average_price) * 100

@dataclass
class Alert:
    id: str
    symbol: str
    type: AlertType
    threshold: Optional[float] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    triggered_at: Optional[datetime] = None
