import asyncio
import feedparser
from typing import List, Optional
from datetime import datetime, timezone
from ...core.interfaces.news_provider import INewsProvider
from ...core.domain.models import NewsArticle, TrendingTopic
from ...core.domain.enums import NewsCategory
from ...core.exceptions import NewsProviderError
import logging

logger = logging.getLogger(__name__)

class RSSNewsProvider(INewsProvider):
    def __init__(self, rss_urls: List[str]):
        self.rss_urls = rss_urls
        if not self.rss_urls:
            logger.warning("No RSS URLs provided to RSSNewsProvider.")

    def _parse_entry(self, entry: feedparser.FeedParserDict) -> NewsArticle:
        pub_date = datetime.now(timezone.utc)
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass

        return NewsArticle(
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            published_at=pub_date,
            source=entry.get("source", {}).get("title", "RSS Feed"),
            summary=entry.get("summary", ""),
        )

    async def _fetch_feed(self, url: str) -> List[NewsArticle]:
        try:
            # feedparser is blocking, run in thread
            def _parse():
                return feedparser.parse(url)
            
            feed = await asyncio.to_thread(_parse)
            if feed.bozo:
                logger.warning(f"Malformed RSS feed {url}: {feed.bozo_exception}")
                # Sometimes bozo is True but entries exist, so we continue
            
            return [self._parse_entry(entry) for entry in feed.entries]
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return []

    async def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        all_articles = await self.get_market_news(limit=50) # fetch more to filter
        filtered = [a for a in all_articles if symbol.lower() in a.title.lower() or (a.summary and symbol.lower() in a.summary.lower())]
        return filtered[:limit]

    async def get_market_news(self, limit: int = 20) -> List[NewsArticle]:
        if not self.rss_urls:
            return []
            
        tasks = [self._fetch_feed(url) for url in self.rss_urls]
        results = await asyncio.gather(*tasks)
        
        all_articles = []
        for r in results:
            all_articles.extend(r)
            
        # Sort by date descending
        all_articles.sort(key=lambda x: x.published_at, reverse=True)
        return all_articles[:limit]

    async def search_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20) -> List[NewsArticle]:
        all_articles = await self.get_market_news(limit=100)
        
        filtered = []
        q_lower = query.lower()
        for a in all_articles:
            if from_date and a.published_at < from_date.replace(tzinfo=timezone.utc): continue
            if to_date and a.published_at > to_date.replace(tzinfo=timezone.utc): continue
                
            if q_lower in a.title.lower() or (a.summary and q_lower in a.summary.lower()):
                filtered.append(a)
                
        return filtered[:limit]

    async def get_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        # RSS provider alone isn't great for trending, return empty and let aggregator handle it or combine
        return []

    async def get_news_by_category(self, category: NewsCategory, limit: int = 20) -> List[NewsArticle]:
        # For RSS, we just use search as a proxy
        query_map = {
            NewsCategory.MARKET: "market OR economy",
            NewsCategory.MACRO: "fed OR rate OR inflation",
            NewsCategory.EARNINGS: "earnings OR revenue",
            NewsCategory.SECTOR: "sector",
            NewsCategory.COMPANY: "shares OR stock",
            NewsCategory.CRYPTO: "crypto OR bitcoin",
            NewsCategory.GENERAL: ""
        }
        return await self.search_news(query=query_map.get(category, ""), limit=limit)
