from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..domain.models import NewsArticle, TrendingTopic
from ..domain.enums import NewsCategory

class INewsAggregator(ABC):
    """Aggregates news from multiple INewsProvider instances."""

    @abstractmethod
    async def get_aggregated_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        """Fetches and deduplicates news for a specific ticker from all providers."""
        pass

    @abstractmethod
    async def get_aggregated_market_news(self, limit: int = 30) -> List[NewsArticle]:
        """Fetches and deduplicates general market news from all providers."""
        pass

    @abstractmethod
    async def search_aggregated_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20) -> List[NewsArticle]:
        """Searches across all providers."""
        pass

    @abstractmethod
    async def get_aggregated_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        """Aggregates trending topics."""
        pass

    @abstractmethod
    async def get_aggregated_news_by_category(self, category: NewsCategory, limit: int = 20) -> List[NewsArticle]:
        """Fetches category news from all providers."""
        pass
