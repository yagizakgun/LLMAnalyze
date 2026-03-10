from abc import ABC, abstractmethod
from ..domain.events import DomainEvent

class INotifier(ABC):
    @abstractmethod
    async def notify(self, event: DomainEvent) -> None:
        """Send a notification for a domain event (e.g. via webhook or email)."""
        pass
