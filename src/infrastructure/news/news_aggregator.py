import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from ...core.interfaces.news_provider import INewsProvider
from ...core.interfaces.news_aggregator import INewsAggregator
from ...core.domain.models import NewsArticle, TrendingTopic
from ...core.domain.enums import NewsCategory
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class NewsAggregator(INewsAggregator):
    def __init__(self, providers: List[INewsProvider]):
        self.providers = providers

    def _deduplicate_and_sort(self, articles: List[NewsArticle], limit: int) -> List[NewsArticle]:
        """Deduplicates articles based on URL and sorts by published_at."""
        unique_urls = set()
        unique_articles = []
        
        # Sort by date first so we keep the newest if there are dupes (unlikely with same URL, but safe)
        articles.sort(key=lambda x: x.published_at, reverse=True)
        
        for article in articles:
            url = article.url
            # Clean URL to avoid trivial duplicates
            parsed = urlparse(url)
            clean_url = f"{parsed.netloc}{parsed.path}"
            
            if clean_url not in unique_urls:
                unique_urls.add(clean_url)
                unique_articles.append(article)
                
        return unique_articles[:limit]

    async def get_aggregated_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        tasks = [p.get_news_for_symbol(symbol, limit) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Aggregator error fetching symbol news: {r}")
            elif isinstance(r, list):
                all_articles.extend(r)
                
        return self._deduplicate_and_sort(all_articles, limit)

    async def get_aggregated_market_news(self, limit: int = 30) -> List[NewsArticle]:
        tasks = [p.get_market_news(limit) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Aggregator error fetching market news: {r}")
            elif isinstance(r, list):
                all_articles.extend(r)
                
        return self._deduplicate_and_sort(all_articles, limit)

    async def search_aggregated_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20) -> List[NewsArticle]:
        tasks = [p.search_news(query, from_date, to_date, limit) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Aggregator error searching news: {r}")
            elif isinstance(r, list):
                all_articles.extend(r)
                
        return self._deduplicate_and_sort(all_articles, limit)

    async def get_aggregated_trending_topics(self, limit: int = 5) -> List[TrendingTopic]:
        tasks = [p.get_trending_topics(limit) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_topics = {} # topic -> TrendingTopic
        
        for r in results:
            if isinstance(r, Exception) or not r:
                continue
            for topic in r:
                if topic.topic in all_topics:
                    all_topics[topic.topic].mention_count += topic.mention_count
                else:
                    all_topics[topic.topic] = topic
                    
        # Sort combined
        sorted_topics = sorted(all_topics.values(), key=lambda x: x.mention_count, reverse=True)
        return sorted_topics[:limit]

    async def get_aggregated_news_by_category(self, category: NewsCategory, limit: int = 20) -> List[NewsArticle]:
        tasks = [p.get_news_by_category(category, limit) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Aggregator error fetching category news: {r}")
            elif isinstance(r, list):
                all_articles.extend(r)
                
        return self._deduplicate_and_sort(all_articles, limit)
