import pytest
from datetime import datetime
from src.core.domain.models import NewsArticle
from src.infrastructure.news.news_aggregator import NewsAggregator

class DummyNewsProvider:
    def __init__(self, prefix: str):
        self.prefix = prefix
        
    async def get_news_for_symbol(self, symbol: str, limit: int = 10):
        return [
            NewsArticle(title=f"{self.prefix} 1 for {symbol}", url=f"http://{self.prefix}.com/1", published_at=datetime(2023, 1, 1), source=self.prefix),
            NewsArticle(title=f"{self.prefix} 2 for {symbol}", url=f"http://{self.prefix}.com/2", published_at=datetime(2023, 1, 2), source=self.prefix)
        ]
        
    async def get_market_news(self, limit: int = 10):
        return [
            NewsArticle(title=f"{self.prefix} Market 1", url=f"http://{self.prefix}.com/m1", published_at=datetime(2023, 1, 1), source=self.prefix),
            # Add a duplicate URL to test deduplication across providers
            NewsArticle(title=f"Shared Market News", url=f"http://shared.com/news1", published_at=datetime(2023, 1, 3), source=self.prefix)
        ]
        
    async def get_trending_topics(self, limit: int = 5):
        from src.core.domain.models import TrendingTopic
        from src.core.domain.enums import Sentiment
        return [
            TrendingTopic(topic=f"Topic_{self.prefix}", mention_count=10, sentiment=Sentiment.NEUTRAL),
            TrendingTopic(topic="Shared_Topic", mention_count=5, sentiment=Sentiment.BULLISH)
        ]

    async def search_news(self, query: str, from_date=None, to_date=None, limit=20):
        return []

    async def get_news_by_category(self, category, limit=20):
        return []

@pytest.mark.asyncio
async def test_aggregator_deduplication():
    p1 = DummyNewsProvider("P1")
    p2 = DummyNewsProvider("P2")
    aggregator = NewsAggregator([p1, p2])
    
    results = await aggregator.get_aggregated_market_news(limit=10)
    
    # Each returns 2 articles, one of which has the same URL (http://shared.com/news1)
    # Total unique should be 3: P1_m1, P2_m1, and Shared
    assert len(results) == 3
    
    urls = [r.url for r in results]
    assert "http://shared.com/news1" in urls
    assert urls.count("http://shared.com/news1") == 1
    
    # Ensure sorted by date descending (Jan 3 is newest)
    assert results[0].url == "http://shared.com/news1"

@pytest.mark.asyncio
async def test_aggregator_trending_topics():
    p1 = DummyNewsProvider("P1")
    p2 = DummyNewsProvider("P2")
    aggregator = NewsAggregator([p1, p2])
    
    topics = await aggregator.get_aggregated_trending_topics(limit=5)
    
    # Shared topic should have counts aggregated (5 + 5 = 10)
    shared_topic = next(t for t in topics if t.topic == "Shared_Topic")
    assert shared_topic.mention_count == 10
