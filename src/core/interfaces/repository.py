from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.models import PortfolioPosition, Alert, AnalysisResult

class IRepository(ABC):
    # Portfolio
    @abstractmethod
    async def get_positions(self) -> List[PortfolioPosition]:
        pass
        
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[PortfolioPosition]:
        pass

    @abstractmethod
    async def save_position(self, position: PortfolioPosition) -> None:
        pass

    @abstractmethod
    async def delete_position(self, symbol: str) -> None:
        pass

    # Alerts
    @abstractmethod
    async def get_active_alerts(self) -> List[Alert]:
        pass

    @abstractmethod
    async def save_alert(self, alert: Alert) -> None:
        pass

    @abstractmethod
    async def update_alert(self, alert: Alert) -> None:
        pass

    # History
    @abstractmethod
    async def save_analysis_result(self, result: AnalysisResult) -> None:
        pass
        
    @abstractmethod
    async def get_analysis_history(self, symbol: str, limit: int = 10) -> List[AnalysisResult]:
        pass
