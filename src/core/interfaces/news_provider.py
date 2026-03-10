from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from typing import List, Optional
from ..domain.models import NewsArticle, TrendingTopic
from ..domain.enums import NewsCategory

class INewsProvider(ABC):
    @abstractmethod
    async def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """Fetches latest news for a specific stock ticker."""
        pass

    @abstractmethod
    async def get_market_news(self, limit: int = 20) -> List[NewsArticle]:
        """Fetches general market news."""
        pass

    @abstractmethod
    async def search_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20) -> List[NewsArticle]:
        """Searches for news articles across the provider."""
        pass

    @abstractmethod
    async def get_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        """Gets trending topics and keywords from recent news."""
        pass

    @abstractmethod
    async def get_news_by_category(self, category: NewsCategory, limit: int = 20) -> List[NewsArticle]:
        """Fetches news for a specific market category."""
        pass
