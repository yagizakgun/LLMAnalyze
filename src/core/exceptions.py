"""Custom exception hierarchy for the LLMAnalyze application."""


class LLMAnalyzeError(Exception):
    """Base exception for all application-specific errors."""
    pass


class MarketDataError(LLMAnalyzeError):
    """Raised when fetching market data fails (e.g., yfinance network error, invalid symbol)."""
    pass


class LLMProviderError(LLMAnalyzeError):
    """Raised when an LLM API call fails (e.g., API key invalid, rate limit, parse error)."""
    pass


class NewsProviderError(LLMAnalyzeError):
    """Raised when fetching news data fails (e.g., NewsAPI key invalid, network error)."""
    pass


class ConfigurationError(LLMAnalyzeError):
    """Raised when required configuration is missing or invalid."""
    pass
