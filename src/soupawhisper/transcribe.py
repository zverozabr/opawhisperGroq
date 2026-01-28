"""Speech-to-text transcription - DEPRECATED.

This module is deprecated. Use soupawhisper.providers instead:

    from soupawhisper.providers import (
        OpenAICompatibleProvider,
        ProviderConfig,
        TranscriptionError,
        TranscriptionResult,
    )
"""

import warnings

# Re-export from providers for backward compatibility
from soupawhisper.constants import GROQ_API_URL
from soupawhisper.providers.base import TranscriptionError, TranscriptionResult
from soupawhisper.providers import OpenAICompatibleProvider, ProviderConfig

__all__ = ["transcribe", "TranscriptionError", "TranscriptionResult", "GROQ_API_URL"]


def transcribe(audio_path: str, api_key: str, model: str, language: str) -> TranscriptionResult:
    """
    Transcribe audio file using Groq Whisper API.

    DEPRECATED: Use OpenAICompatibleProvider instead:

        from soupawhisper.providers import OpenAICompatibleProvider, ProviderConfig

        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=api_key,
            model=model,
        )
        provider = OpenAICompatibleProvider(config)
        result = provider.transcribe(audio_path, language)

    Args:
        audio_path: Path to audio file (WAV format)
        api_key: Groq API key
        model: Whisper model name
        language: Language code (e.g., "ru", "en") or "auto" for auto-detection

    Returns:
        TranscriptionResult with text and raw API response

    Raises:
        TranscriptionError: If API call fails
    """
    warnings.warn(
        "transcribe() is deprecated. Use OpenAICompatibleProvider instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = ProviderConfig(
        name="groq-legacy",
        type="openai_compatible",
        url=GROQ_API_URL,
        api_key=api_key,
        model=model,
    )
    provider = OpenAICompatibleProvider(config)
    return provider.transcribe(audio_path, language)
