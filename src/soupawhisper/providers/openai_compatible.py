"""OpenAI-compatible transcription provider.

Works with: Groq, OpenAI, Together, Fireworks, DeepInfra, and any other
service that implements the OpenAI /v1/audio/transcriptions endpoint.
"""

import requests

from soupawhisper.providers.base import ProviderConfig, TranscriptionError, TranscriptionResult


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible transcription APIs.

    Supports any service with /v1/audio/transcriptions endpoint:
    - Groq: https://api.groq.com/openai/v1/audio/transcriptions
    - OpenAI: https://api.openai.com/v1/audio/transcriptions
    - Together: https://api.together.xyz/v1/audio/transcriptions
    - Fireworks: https://audio-prod.api.fireworks.ai/v1/audio/transcriptions
    - DeepInfra: https://api.deepinfra.com/v1/inference/openai/whisper-large-v3
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider with configuration.

        Args:
            config: Provider configuration with url, api_key, model
        """
        self._config = config

    @property
    def name(self) -> str:
        """Provider name."""
        return self._config.name

    def is_available(self) -> bool:
        """Check if provider is configured (has url and api_key)."""
        return bool(self._config.url and self._config.api_key)

    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio file using OpenAI-compatible API.

        Args:
            audio_path: Path to audio file (WAV format preferred)
            language: Language code (e.g., "ru", "en") or "auto" for auto-detection

        Returns:
            TranscriptionResult with text and raw API response

        Raises:
            TranscriptionError: If API call fails or provider not configured
        """
        if not self._config.url:
            raise TranscriptionError(f"Provider '{self.name}' has no URL configured")
        if not self._config.api_key:
            raise TranscriptionError(f"Provider '{self.name}' has no API key configured")

        headers = {"Authorization": f"Bearer {self._config.api_key}"}

        data: dict[str, str] = {"model": self._config.model}
        if language != "auto":
            data["language"] = language

        try:
            with open(audio_path, "rb") as f:
                response = requests.post(
                    self._config.url,
                    headers=headers,
                    files={"file": ("audio.wav", f, "audio/wav")},
                    data=data,
                    timeout=30,
                )
        except requests.RequestException as e:
            raise TranscriptionError(f"Network error: {e}") from e

        if not response.ok:
            raise TranscriptionError(f"API error {response.status_code}: {response.text}")

        response_json = response.json()
        return TranscriptionResult(
            text=response_json.get("text", "").strip(),
            raw_response=response_json,
        )
