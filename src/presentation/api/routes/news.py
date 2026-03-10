from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from ..dependencies import get_news_service
from ....application.services.news_service import NewsService
from ....core.domain.enums import NewsCategory, LLMProviderType
from ..schemas import NewsArticleResponse, TrendingTopicResponse, NewsImpactResponse, NewsSummaryResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/market", response_model=List[NewsArticleResponse])
async def get_market_news(
    limit: int = Query(30, description="Max number of articles"),
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for sentiment"),
    news_service: NewsService = Depends(get_news_service)
):
    """Get general aggregated market news with sentiment analysis."""
    try:
        return await news_service.get_market_news(limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/market endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error fetching market news.")

@router.get("/summary", response_model=NewsSummaryResponse)
async def get_market_summary(
    limit: int = Query(20, description="Max number of articles for summary context"),
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for sentiment"),
    news_service: NewsService = Depends(get_news_service)
):
    """Get a high-level market summary combining news and trending topics."""
    try:
        return await news_service.get_market_summary(limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/summary endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error generating market summary.")

@router.get("/trending", response_model=List[TrendingTopicResponse])
async def get_trending_topics(
    limit: int = Query(10, description="Max number of topics"),
    llm: Optional[LLMProviderType] = Query(None, description="Optional LLM to use for better topic extraction"),
    news_service: NewsService = Depends(get_news_service)
):
    """Get current trending topics in the news."""
    try:
        return await news_service.get_trending_topics(limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/trending endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error fetching trending topics.")

@router.get("/search", response_model=List[NewsArticleResponse])
async def search_news(
    query: str = Query(..., description="Search query"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(20, description="Max number of articles"),
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for sentiment"),
    news_service: NewsService = Depends(get_news_service)
):
    """Search for news across all providers."""
    try:
        return await news_service.search_news(query, from_date, to_date, limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error searching news.")

@router.get("/category/{category}", response_model=List[NewsArticleResponse])
async def get_category_news(
    category: NewsCategory,
    limit: int = Query(20, description="Max number of articles"),
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for sentiment"),
    news_service: NewsService = Depends(get_news_service)
):
    """Get news for a specific market category."""
    try:
        return await news_service.get_category_news(category, limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/category endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error fetching category news.")

@router.get("/{symbol}", response_model=List[NewsArticleResponse])
async def get_symbol_news(
    symbol: str,
    limit: int = Query(20, description="Max number of articles"),
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for sentiment"),
    news_service: NewsService = Depends(get_news_service)
):
    """Get recent news for a specific stock ticker."""
    try:
        return await news_service.get_symbol_news(symbol, limit, llm)
    except Exception as e:
        logger.error(f"Error in /news/symbol endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error fetching symbol news.")

@router.get("/{symbol}/impact", response_model=NewsImpactResponse)
async def analyze_news_impact(
    symbol: str,
    llm: LLMProviderType = Query(LLMProviderType.OPENAI, description="LLM to use for impact analysis"),
    news_service: NewsService = Depends(get_news_service)
):
    """Analyze the potential market impact of recent news for a stock using an LLM."""
    try:
        return await news_service.analyze_news_impact(symbol, llm)
    except Exception as e:
        logger.error(f"Error in /news/impact endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing news impact.")
