import pytest
from src.infrastructure.news.rss_provider import RSSNewsProvider

@pytest.mark.asyncio
async def test_rss_provider_empty():
    provider = RSSNewsProvider(rss_urls=[])
    news = await provider.get_market_news(limit=10)
    assert news == []
    
@pytest.mark.asyncio
async def test_rss_provider_invalid_url():
    provider = RSSNewsProvider(rss_urls=["http://invalid.url.that.does.not.exist"])
    news = await provider.get_market_news(limit=10)
    # The provider should catch the exception and return returning an empty list
    # or just log an error depending on feedparser behavior
    assert isinstance(news, list)
