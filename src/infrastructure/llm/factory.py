from typing import Dict
from ...core.interfaces.llm_provider import ILLMProvider
from ...core.domain.enums import LLMProviderType
from ...core.config import Settings
from .openai_provider import OpenAIProvider
from .mock_provider import MockLLMProvider
from .gemini_provider import GeminiProvider


class LLMFactory:
    """Factory to instantiate the appropriate ILLMProvider based on the requested type."""

    def __init__(self, settings: Settings = None):
        self._settings = settings or Settings()
        self._providers: Dict[LLMProviderType, ILLMProvider] = {}

    def get_provider(self, provider_type: LLMProviderType) -> ILLMProvider:
        """Returns the appropriate LLM provider instance."""

        if provider_type in self._providers:
            return self._providers[provider_type]

        if provider_type == LLMProviderType.OPENAI:
            provider = OpenAIProvider(api_key=self._settings.openai_api_key)
        elif provider_type == LLMProviderType.MOCK:
            provider = MockLLMProvider()
        elif provider_type == LLMProviderType.GEMINI:
            provider = GeminiProvider(api_key=self._settings.gemini_api_key)
        else:
            raise ValueError(f"Unsupported LLM Provider Type: {provider_type}")

        self._providers[provider_type] = provider
        return provider
