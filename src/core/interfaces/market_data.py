from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.enums import TimeFrame
from ..domain.models import OHLCV, StockInfo


class IMarketDataProvider(ABC):
    @abstractmethod
    async def get_stock_data(self, symbol: str, timeframe: TimeFrame, limit: int = 100) -> List[OHLCV]:
        """Fetches historical price and volume data."""
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """Fetches the latest real-time or delayed price."""
        pass

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> StockInfo:
        """Fetches company profile and basic info."""
        pass

    @abstractmethod
    async def get_stock_fundamentals(self, symbol: str) -> Optional[dict]:
        """Fetch fundamental analysis data (P/E, P/B, dividend yield, etc.)."""
        pass

    @abstractmethod
    async def get_analyst_data(self, symbol: str) -> Optional[dict]:
        """Fetch analyst price targets and recommendations."""
        pass
