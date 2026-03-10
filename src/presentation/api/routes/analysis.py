from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_analysis_service
from ....application.services.analysis_service import AnalysisService
from ....core.domain.enums import TimeFrame, LLMProviderType
from ....core.exceptions import MarketDataError, LLMProviderError, NewsProviderError
from ..schemas import AnalysisResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{symbol}", response_model=AnalysisResponse)
async def get_full_analysis(
    symbol: str,
    timeframe: TimeFrame = TimeFrame.D1,
    llm_provider: LLMProviderType = LLMProviderType.OPENAI,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Returns a comprehensive analysis for the given stock symbol.
    Queries market data, technicals, news, and LLM concurrently.
    """
    try:
        result = await service.run_full_analysis(symbol.upper(), timeframe, llm_provider)
        return result
    except MarketDataError as e:
        logger.error(f"Market data error for {symbol}: {e}")
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {e}")
    except LLMProviderError as e:
        logger.error(f"LLM provider error for {symbol}: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except NewsProviderError as e:
        logger.error(f"News provider error for {symbol}: {e}")
        raise HTTPException(status_code=502, detail=f"News service unavailable: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during analysis of {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
