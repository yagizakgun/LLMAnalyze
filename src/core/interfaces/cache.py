from abc import ABC, abstractmethod
from typing import Any, Optional

class ICacheProvider(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a value with an optional time-to-live."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a given key."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached data."""
        pass
