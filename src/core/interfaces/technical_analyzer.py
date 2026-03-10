from abc import ABC, abstractmethod
from typing import List
from ..domain.models import OHLCV, TechnicalIndicators, Signal

class ITechnicalAnalyzer(ABC):
    @abstractmethod
    def calculate_indicators(self, data: List[OHLCV]) -> TechnicalIndicators:
        """Calculates a comprehensive set of technical indicators."""
        pass

    @abstractmethod
    def generate_signal(self, symbol: str, data: List[OHLCV], indicators: TechnicalIndicators) -> Signal:
        """Evaluates indicators to produce a BUY, SELL, or HOLD signal."""
        pass
