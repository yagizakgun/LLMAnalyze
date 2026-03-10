from functools import lru_cache
from typing import Union
from ...core.config import Settings
from ...core.domain.enums import MarketDataProviderType
from ...infrastructure.llm.factory import LLMFactory
from ...infrastructure.market_data.yahoo_provider import YahooFinanceProvider
from ...infrastructure.market_data.borsapy_provider import BorsapyProvider
from ...infrastructure.news.newsapi_provider import NewsAPIProvider
from ...infrastructure.news.rss_provider import RSSNewsProvider
from ...infrastructure.news.news_aggregator import NewsAggregator
from ...infrastructure.analysis.ta_engine import TAEngine
from ...application.services.analysis_service import AnalysisService
from ...application.services.news_service import NewsService
from ...core.interfaces.market_data import IMarketDataProvider


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
def get_borsapy_provider() -> BorsapyProvider:
    return BorsapyProvider()


def get_configured_market_provider() -> Union[YahooFinanceProvider, BorsapyProvider]:
    """Returns the market data provider based on configuration settings."""
    settings = get_settings()
    if settings.default_market_provider == "borsapy":
        return get_borsapy_provider()
    return get_market_provider()


def get_market_provider_by_type(provider_type: MarketDataProviderType) -> IMarketDataProvider:
    """Returns the market data provider based on the given type."""
    if provider_type == MarketDataProviderType.BORSAPY:
        return get_borsapy_provider()
    return get_market_provider()


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
        market_data=get_configured_market_provider(),
        news=get_news_provider(), # We keep using the single provider or switch to aggregator if needed
        ta=get_ta_engine(),
    )
