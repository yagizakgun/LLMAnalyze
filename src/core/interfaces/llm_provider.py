from abc import ABC, abstractmethod
from typing import Dict, List
from ..domain.models import AnalysisResult, SentimentResult, LLMAnalysisResult, NewsImpactAnalysis, NewsArticle, TrendingTopic

class ILLMProvider(ABC):
    @abstractmethod
    async def analyze_stock(self, context_data: Dict) -> LLMAnalysisResult:
        """Analyzes stock data and returns a structured LLM result."""
        pass

    @abstractmethod
    async def analyze_sentiment(self, texts: List[str]) -> SentimentResult:
        """Analyzes sentiment of multiple texts."""
        pass

    @abstractmethod
    async def analyze_article_sentiments(self, articles: List[Dict]) -> List[Dict]:
        """Analyzes sentiment and metadata per news article.
        
        Args:
            articles: List of dicts with 'title' and 'summary' keys.
        
        Returns:
            List of dicts with:
                - 'index': (int) original index
                - 'sentiment': (str) "BULLISH", "BEARISH", or "NEUTRAL"
                - 'score': (float) -1.0 to 1.0
                - 'category': (str) matching NewsCategory enum values
                - 'keywords': (List[str]) key terms
                - 'relevance_score': (float) 0.0 to 1.0
        """
        pass

    @abstractmethod
    async def analyze_news_impact(self, symbol: str, articles: List[NewsArticle]) -> NewsImpactAnalysis:
        """Analyzes the combined impact of recent news on a specific stock."""
        pass

    @abstractmethod
    async def extract_trending_topics(self, articles: List[Dict], limit: int = 5) -> List[TrendingTopic]:
        """Extracts trending topics from a list of news articles."""
        pass

    @abstractmethod
    async def generate_report(self, analysis: AnalysisResult) -> str:
        """Generates a comprehensive readable report from analysis."""
        pass
