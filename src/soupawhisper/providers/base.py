"""Base protocol and config for transcription providers."""

from dataclasses import dataclass
from typing import Any, Protocol

from soupawhisper.constants import DEFAULT_MODEL


@dataclass
class TranscriptionResult:
    """Result from transcription provider."""

    text: str
    raw_response: dict[str, Any]


@dataclass
class ProviderConfig:
    """Configuration for a transcription provider."""

    name: str
    type: str  # "openai_compatible" | "mlx"
    url: str | None = None
    api_key: str | None = None
    model: str = DEFAULT_MODEL

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "ProviderConfig":
        """Create ProviderConfig from dictionary."""
        return cls(
            name=name,
            type=data.get("type", "openai_compatible"),
            url=data.get("url"),
            api_key=data.get("api_key"),
            model=data.get("model", DEFAULT_MODEL),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {"type": self.type}
        if self.url:
            result["url"] = self.url
        if self.api_key:
            result["api_key"] = self.api_key
        if self.model:
            result["model"] = self.model
        return result


class TranscriptionProvider(Protocol):
    """Protocol for transcription providers.

    All providers must implement this interface.
    """

    @property
    def name(self) -> str:
        """Provider name."""
        ...

    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio file.

        Args:
            audio_path: Path to audio file
            language: Language code or "auto" for auto-detection

        Returns:
            TranscriptionResult with text and raw response

        Raises:
            TranscriptionError: If transcription fails
        """
        ...

    def is_available(self) -> bool:
        """Check if provider is available (dependencies installed, etc.)."""
        ...


class TranscriptionError(Exception):
    """Raised when transcription fails."""
