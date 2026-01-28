"""Provider registry for transcription providers."""

from typing import Callable

from soupawhisper.providers.base import ProviderConfig, TranscriptionProvider


class ProviderRegistry:
    """Registry for provider factories."""

    _factories: dict[str, Callable[[ProviderConfig], TranscriptionProvider]] = {}

    @classmethod
    def register(
        cls, provider_type: str, factory: Callable[[ProviderConfig], TranscriptionProvider]
    ) -> None:
        cls._factories[provider_type] = factory

    @classmethod
    def create(cls, config: ProviderConfig) -> TranscriptionProvider:
        factory = cls._factories.get(config.type)
        if factory is None:
            raise ValueError(f"Unknown provider type: {config.type}")
        return factory(config)

    @classmethod
    def list_types(cls) -> list[str]:
        return sorted(cls._factories.keys())
