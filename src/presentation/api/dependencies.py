from functools import lru_cache
from ...core.config import Settings
from ...infrastructure.llm.factory import LLMFactory
from ...infrastructure.market_data.yahoo_provider import YahooFinanceProvider
from ...infrastructure.news.newsapi_provider import NewsAPIProvider
from ...infrastructure.news.rss_provider import RSSNewsProvider
from ...infrastructure.news.news_aggregator import NewsAggregator
from ...infrastructure.analysis.ta_engine import TAEngine
from ...application.services.analysis_service import AnalysisService
from ...application.services.news_service import NewsService


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_llm_factory() -> LLMFactory:
    settings = get_settings()
    return LLMFactory(settings=settings)


@lru_cache
def get_market_provider() -> YahooFinanceProvider:
    return YahooFinanceProvider()


@lru_cache
def get_news_provider() -> NewsAPIProvider:
    settings = get_settings()
    return NewsAPIProvider(api_key=settings.newsapi_key)


@lru_cache
def get_rss_provider() -> RSSNewsProvider:
    # We can add feed URLs via settings if desired, hardcoding a few reliable ones for now
    rss_urls = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://cointelegraph.com/rss"
    ]
    return RSSNewsProvider(rss_urls=rss_urls)


@lru_cache
def get_news_aggregator() -> NewsAggregator:
    # Combine providers
    providers = []
    newsapi = get_news_provider()
    # If NewsAPI key is set, add it
    if newsapi.api_key:
        providers.append(newsapi)
    providers.append(get_rss_provider())
    return NewsAggregator(providers=providers)


@lru_cache
def get_news_service() -> NewsService:
    return NewsService(
        aggregator=get_news_aggregator(),
        llm_factory=get_llm_factory()
    )


@lru_cache
def get_ta_engine() -> TAEngine:
    return TAEngine()


@lru_cache
def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        llm_factory=get_llm_factory(),
        market_data=get_market_provider(),
        news=get_news_provider(), # We keep using the single provider or switch to aggregator if needed
        ta=get_ta_engine(),
    )
