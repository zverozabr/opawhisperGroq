"""MLX-based local transcription provider for macOS Apple Silicon."""

import logging
import sys
from typing import Any

from soupawhisper.providers.base import ProviderConfig, TranscriptionError, TranscriptionResult

logger = logging.getLogger(__name__)


class MLXProvider:
    """Local transcription provider using mlx-whisper.

    Only available on macOS with Apple Silicon (M1/M2/M3/M4).
    Requires: pip install mlx-whisper

    Uses HuggingFace models from mlx-community, e.g.:
    - mlx-community/whisper-tiny-mlx
    - mlx-community/whisper-large-v3-mlx
    - mlx-community/whisper-large-v3-turbo
    """

    # Default model if not specified in config
    DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize MLX provider.

        Args:
            config: Provider configuration with model name (HuggingFace repo)
        """
        self._config = config
        # Ensure model has full HF path
        if self._config.model and "/" not in self._config.model:
            # Convert short name to full HF repo path
            self._model_repo = f"mlx-community/whisper-{self._config.model}-mlx"
        else:
            self._model_repo = self._config.model or self.DEFAULT_MODEL

    @property
    def name(self) -> str:
        """Provider name."""
        return self._config.name

    @property
    def model(self) -> str:
        """Model HuggingFace repo."""
        return self._model_repo

    def is_available(self) -> bool:
        """Check if MLX is available (macOS + library installed)."""
        if sys.platform != "darwin":
            return False
        try:
            import mlx_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio file using local MLX Whisper.

        Args:
            audio_path: Path to audio file
            language: Language code ("auto" for auto-detection)

        Returns:
            TranscriptionResult with text and raw response

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_available():
            raise TranscriptionError("MLX provider not available on this platform")

        try:
            import mlx_whisper

            logger.info(f"Transcribing with MLX model: {self._model_repo}")

            # mlx_whisper.transcribe returns dict with 'text', 'segments', 'language'
            result: dict[str, Any] = mlx_whisper.transcribe(
                audio_path,
                path_or_hf_repo=self._model_repo,
                language=None if language == "auto" else language,
            )

            text = result.get("text", "")
            if not isinstance(text, str):
                text = str(text)

            return TranscriptionResult(
                text=text.strip(),
                raw_response=result,
            )

        except ImportError as e:
            raise TranscriptionError(
                "mlx-whisper not installed. "
                "Install with: pip install mlx-whisper"
            ) from e
        except Exception as e:
            raise TranscriptionError(f"MLX transcription failed: {e}") from e
