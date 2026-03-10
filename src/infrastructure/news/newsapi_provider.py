import httpx
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from ...core.interfaces.news_provider import INewsProvider
from ...core.domain.models import NewsArticle, TrendingTopic
from ...core.domain.enums import NewsCategory
from ...core.exceptions import NewsProviderError
import logging

logger = logging.getLogger(__name__)


class NewsAPIProvider(INewsProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        if not self.api_key:
            logger.warning("NEWSAPI_KEY is not set.")

    def _parse_article(self, item: dict) -> NewsArticle:
        """Parse a single article from the NewsAPI response."""
        pub_str = item.get("publishedAt", "")
        try:
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        except ValueError:
            pub_dt = datetime.now(timezone.utc)

        return NewsArticle(
            title=item.get("title", ""),
            url=item.get("url", ""),
            published_at=pub_dt,
            source=item.get("source", {}).get("name", "Unknown"),
            summary=item.get("description", ""),
        )

    async def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        if not self.api_key:
            return []

        try:
            query = f"{symbol} stock"
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.api_key,
                "pageSize": limit,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return [self._parse_article(item) for item in data.get("articles", [])]
        except httpx.HTTPStatusError as e:
            logger.error(f"NewsAPI HTTP error for {symbol}: {e.response.status_code}")
            raise NewsProviderError(f"NewsAPI HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"NewsAPI network error for {symbol}: {e}")
            raise NewsProviderError(f"NewsAPI network error: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    async def search_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20) -> List[NewsArticle]:
        if not self.api_key:
            return []
            
        try:
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "sortBy": "relevancy",
                "language": "en",
                "apiKey": self.api_key,
                "pageSize": limit,
            }
            if from_date:
                params["from"] = from_date.strftime("%Y-%m-%d")
            if to_date:
                params["to"] = to_date.strftime("%Y-%m-%d")
                
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return [self._parse_article(item) for item in data.get("articles", [])]
        except Exception as e:
            logger.error(f"Error searching news for {query}: {e}")
            return []

    async def get_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        # NewsAPI doesn't have a direct "trending" endpoint, so we infer from top headlines
        if not self.api_key:
            return []
            
        articles = await self.get_market_news(limit=50)
        # Very basic topic extraction (mock-like for now until we use NLP)
        topics = {}
        for a in articles:
            words = [w for w in a.title.split() if len(w) > 5 and w[0].isupper()]
            for w in words:
                topics[w] = topics.get(w, 0) + 1
                
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:limit]
        from ...core.domain.enums import Sentiment
        return [
            TrendingTopic(topic=t[0], mention_count=t[1], sentiment=Sentiment.NEUTRAL)
            for t in sorted_topics if t[1] > 1
        ]

    async def get_news_by_category(self, category: NewsCategory, limit: int = 20) -> List[NewsArticle]:
        if not self.api_key:
            return []
            
        category_map = {
            NewsCategory.MARKET: "business",
            NewsCategory.MACRO: "business",
            NewsCategory.EARNINGS: "business", # NewsAPI top headlines uses specific categories
            NewsCategory.SECTOR: "business",
            NewsCategory.COMPANY: "business",
            NewsCategory.CRYPTO: "technology",
            NewsCategory.GENERAL: "general"
        }
        
        # Use top-headlines with category for market/macro/general
        if category in [NewsCategory.MARKET, NewsCategory.GENERAL, NewsCategory.MACRO]:
            try:
                url = f"{self.base_url}/top-headlines"
                params = {
                    "category": category_map.get(category, "business"),
                    "country": "us",
                    "apiKey": self.api_key,
                    "pageSize": limit,
                }
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    return [self._parse_article(item) for item in data.get("articles", [])]
            except Exception as e:
                logger.error(f"Error fetching category news {category}: {e}")
                return []
        
        # Use everything with query for others
        query_map = {
            NewsCategory.CRYPTO: "cryptocurrency OR bitcoin OR ethereum",
            NewsCategory.EARNINGS: "earnings report revenue CEO",
            NewsCategory.SECTOR: "tech OR energy OR healthcare sector stock",
            NewsCategory.COMPANY: "company stock shares"
        }
        return await self.search_news(query=query_map.get(category, "business"), limit=limit)

    async def get_market_news(self, limit: int = 20) -> List[NewsArticle]:
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/top-headlines"
            params = {
                "category": "business",
                "country": "us",
                "apiKey": self.api_key,
                "pageSize": limit,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return [self._parse_article(item) for item in data.get("articles", [])]
        except httpx.HTTPStatusError as e:
            logger.error(f"NewsAPI HTTP error for market news: {e.response.status_code}")
            raise NewsProviderError(f"NewsAPI HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"NewsAPI network error for market news: {e}")
            raise NewsProviderError(f"NewsAPI network error: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []
