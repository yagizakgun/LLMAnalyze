import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.core.domain.models import NewsArticle, NewsImpactAnalysis, TrendingTopic
from src.core.domain.enums import Sentiment, LLMProviderType
from src.application.services.news_service import NewsService

@pytest.mark.asyncio
async def test_news_service_enrichment():
    mock_aggregator = AsyncMock()
    mock_aggregator.get_aggregated_news.return_value = [
        NewsArticle(title="Good news", url="http://1", published_at=datetime.now(), source="Src1"),
        NewsArticle(title="Bad news", url="http://2", published_at=datetime.now(), source="Src2")
    ]
    
    mock_llm = AsyncMock()
    mock_llm.analyze_article_sentiments.return_value = [
        {"index": 0, "sentiment": "BULLISH", "score": 0.8},
        {"index": 1, "sentiment": "BEARISH", "score": -0.5}
    ]
    
    mock_factory = MagicMock()
    mock_factory.get_provider.return_value = mock_llm
    
    service = NewsService(aggregator=mock_aggregator, llm_factory=mock_factory)
    
    articles = await service.get_symbol_news("AAPL")
    
    assert len(articles) == 2
    assert articles[0].sentiment == Sentiment.BULLISH
    assert articles[0].sentiment_score == 0.8
    assert articles[1].sentiment == Sentiment.BEARISH
    assert articles[1].sentiment_score == -0.5
    
@pytest.mark.asyncio
async def test_news_service_impact():
    mock_aggregator = AsyncMock()
    mock_aggregator.get_aggregated_news.return_value = [
        NewsArticle(title="News", url="http://1", published_at=datetime.now(), source="Src1")
    ]
    
    mock_llm = AsyncMock()
    mock_llm.analyze_news_impact.return_value = NewsImpactAnalysis(
        impact_score=0.9, price_impact_prediction="Up", confidence=0.8, reasoning="Good", affected_sectors=[]
    )
    
    mock_factory = MagicMock()
    mock_factory.get_provider.return_value = mock_llm
    
    service = NewsService(aggregator=mock_aggregator, llm_factory=mock_factory)
    
    impact = await service.analyze_news_impact("AAPL")
    
    assert impact.impact_score == 0.9
    assert impact.impact_score == 0.9
    assert impact.price_impact_prediction == "Up"

@pytest.mark.asyncio
async def test_news_service_enriched_metadata():
    mock_aggregator = AsyncMock()
    mock_aggregator.get_aggregated_news.return_value = [
        NewsArticle(title="Company X profits up", url="http://1", published_at=datetime.now(), source="Src1"),
    ]
    
    mock_llm = AsyncMock()
    mock_llm.analyze_article_sentiments.return_value = [
        {
            "index": 0, 
            "sentiment": "BULLISH", 
            "score": 0.8,
            "category": "EARNINGS",
            "keywords": ["profits", "growth"],
            "relevance_score": 0.9
        }
    ]
    
    mock_factory = MagicMock()
    mock_factory.get_provider.return_value = mock_llm
    
    service = NewsService(aggregator=mock_aggregator, llm_factory=mock_factory)
    
    articles = await service.get_symbol_news("AAPL")
    
    assert len(articles) == 1
    article = articles[0]
    from src.core.domain.enums import NewsCategory
    assert article.category == NewsCategory.EARNINGS
    assert article.keywords == ["profits", "growth"]
    assert article.relevance_score == 0.9

@pytest.mark.asyncio
async def test_news_service_trending_llm():
    mock_aggregator = AsyncMock()
    mock_aggregator.get_aggregated_market_news.return_value = [
        NewsArticle(title="AI Trends", url="http://1", published_at=datetime.now(), source="Src1")
    ]
    
    mock_llm = AsyncMock()
    mock_llm.extract_trending_topics.return_value = [
        TrendingTopic(topic="AI", mention_count=10, sentiment=Sentiment.BULLISH)
    ]
    
    mock_factory = MagicMock()
    mock_factory.get_provider.return_value = mock_llm
    
    service = NewsService(aggregator=mock_aggregator, llm_factory=mock_factory)
    
    topics = await service.get_trending_topics(limit=5, llm_provider=LLMProviderType.MOCK)
    
    assert len(topics) == 1
    assert topics[0].topic == "AI"
    assert topics[0].sentiment == Sentiment.BULLISH
    mock_llm.extract_trending_topics.assert_called_once()
