import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from ...core.domain.models import NewsArticle, TrendingTopic, NewsImpactAnalysis, NewsSummary
from ...core.domain.enums import NewsCategory, Sentiment
from ...core.interfaces.news_aggregator import INewsAggregator
from ...infrastructure.llm.factory import LLMFactory
from ...core.domain.enums import LLMProviderType
import logging

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, aggregator: INewsAggregator, llm_factory: LLMFactory):
        self.aggregator = aggregator
        self.llm_factory = llm_factory

    async def _enrich_with_sentiment(self, articles: List[NewsArticle], llm_provider: LLMProviderType) -> List[NewsArticle]:
        """Enriches a list of articles with sentiment analysis using the LLM."""
        if not articles:
            return []
            
        try:
            llm = self.llm_factory.get_provider(llm_provider)
            
            article_dicts = [
                {"title": a.title, "summary": a.summary or ""} for a in articles
            ]
            
            sentiments = await llm.analyze_article_sentiments(article_dicts)
            
            sentiment_map = {item["index"]: item for item in sentiments}
            for i, article in enumerate(articles):
                if i in sentiment_map:
                    entry = sentiment_map[i]
                    try:
                        article.sentiment = Sentiment(entry["sentiment"])
                    except ValueError:
                        article.sentiment = Sentiment.NEUTRAL
                    article.sentiment_score = entry["score"]
                    article.relevance_score = entry.get("relevance_score")
                    article.keywords = entry.get("keywords", [])
                    
                    cat_str = entry.get("category")
                    if cat_str:
                        try:
                            article.category = NewsCategory(cat_str.upper())
                        except ValueError:
                            article.category = NewsCategory.GENERAL
                    
            return articles
        except Exception as e:
            logger.error(f"Error enriching articles with sentiment: {e}")
            return articles

    async def get_symbol_news(self, symbol: str, limit: int = 20, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> List[NewsArticle]:
        """Gets news for a specific symbol, enriched with sentiment."""
        articles = await self.aggregator.get_aggregated_news(symbol, limit)
        return await self._enrich_with_sentiment(articles, llm_provider)

    async def get_market_news(self, limit: int = 30, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> List[NewsArticle]:
        """Gets general market news, enriched with sentiment."""
        articles = await self.aggregator.get_aggregated_market_news(limit)
        return await self._enrich_with_sentiment(articles, llm_provider)
        
    async def get_market_summary(self, limit: int = 20, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> NewsSummary:
        """Gets a comprehensive market summary including overall sentiment and topics."""
        articles = await self.get_market_news(limit=limit, llm_provider=llm_provider)
        topics = await self.get_trending_topics(limit=5)
        
        # Calculate overall sentiment from articles
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        overall = Sentiment.NEUTRAL
        if avg_score > 0.2: overall = Sentiment.BULLISH
        elif avg_score < -0.2: overall = Sentiment.BEARISH
        
        return NewsSummary(
            timestamp=datetime.now(timezone.utc),
            market_status="OPEN" if datetime.now(timezone.utc).weekday() < 5 else "CLOSED",
            key_events=[a.title for a in articles[:5]],
            overall_sentiment=overall,
            trending_topics=topics
        )

    async def search_news(self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 20, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> List[NewsArticle]:
        """Searches for news and enriches with sentiment."""
        articles = await self.aggregator.search_aggregated_news(query, from_date, to_date, limit)
        return await self._enrich_with_sentiment(articles, llm_provider)

    async def get_trending_topics(self, limit: int = 5, llm_provider: Optional[LLMProviderType] = None) -> List[TrendingTopic]:
        """Gets trending topics, optionally using an LLM for better extraction."""
        if llm_provider:
            # Fetch more articles to give the LLM better context for trending themes
            articles = await self.aggregator.get_aggregated_market_news(limit=50)
            if not articles:
                return []
                
            llm = self.llm_factory.get_provider(llm_provider)
            article_dicts = [{"title": a.title, "summary": a.summary or ""} for a in articles]
            return await llm.extract_trending_topics(article_dicts, limit=limit)
            
        return await self.aggregator.get_aggregated_trending_topics(limit)

    async def get_category_news(self, category: NewsCategory, limit: int = 20, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> List[NewsArticle]:
        """Gets news by category and enriches with sentiment."""
        articles = await self.aggregator.get_aggregated_news_by_category(category, limit)
        return await self._enrich_with_sentiment(articles, llm_provider)

    async def analyze_news_impact(self, symbol: str, llm_provider: LLMProviderType = LLMProviderType.OPENAI) -> NewsImpactAnalysis:
        """Analyzes the collective impact of recent news on a stock using LLM."""
        articles = await self.aggregator.get_aggregated_news(symbol, limit=10)
        
        if not articles:
            return NewsImpactAnalysis(
                impact_score=0.0,
                price_impact_prediction="No recent news",
                confidence=1.0,
                reasoning="No news available to analyze impact.",
                affected_sectors=[]
            )
            
        llm = self.llm_factory.get_provider(llm_provider)
        return await llm.analyze_news_impact(symbol, articles)
