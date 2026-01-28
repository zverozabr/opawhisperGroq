"""Cross-platform local transcription provider using faster-whisper."""

import logging
from typing import Any

from soupawhisper.providers.base import ProviderConfig, TranscriptionError, TranscriptionResult

logger = logging.getLogger(__name__)


class FasterWhisperProvider:
    """Cross-platform local transcription provider using faster-whisper.

    Works on Linux, Windows, and macOS (Intel or Apple Silicon fallback).
    Uses CTranslate2 for optimized inference.

    GPU Support:
    - NVIDIA: CUDA acceleration (requires CUDA toolkit)
    - CPU: Works everywhere, uses int8 quantization for speed

    Requires: pip install faster-whisper

    Models are automatically downloaded from HuggingFace on first use.
    Available models: tiny, base, small, medium, large-v3, large-v3-turbo
    """

    # Default model if not specified
    DEFAULT_MODEL = "large-v3-turbo"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize faster-whisper provider.

        Args:
            config: Provider configuration with model name
        """
        self._config = config
        self._model: Any = None
        # Extract model name (strip any HF repo prefix)
        model = self._config.model or self.DEFAULT_MODEL
        if "/" in model:
            # Convert HF repo to model name: "Systran/faster-whisper-large-v3" -> "large-v3"
            model = model.split("/")[-1].replace("faster-whisper-", "")
        self._model_name = model

        # Device configuration from config or auto-detect
        self._device = getattr(config, "device", None) or "auto"
        self._compute_type = getattr(config, "compute_type", None) or "auto"

    @property
    def name(self) -> str:
        """Provider name."""
        return self._config.name

    @property
    def model(self) -> str:
        """Model name."""
        return self._model_name

    def is_available(self) -> bool:
        """Check if faster-whisper is available."""
        try:
            import faster_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_model(self) -> Any:
        """Lazy-load the Whisper model.

        Returns:
            WhisperModel instance

        Raises:
            TranscriptionError: If model loading fails
        """
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    f"Loading faster-whisper model: {self._model_name} "
                    f"(device={self._device}, compute_type={self._compute_type})"
                )

                # Determine device and compute type
                device = self._device
                compute_type = self._compute_type

                if device == "auto":
                    # Auto-detect: try CUDA first, fall back to CPU
                    try:
                        import torch

                        device = "cuda" if torch.cuda.is_available() else "cpu"
                    except ImportError:
                        device = "cpu"

                if compute_type == "auto":
                    # Use float16 for GPU, int8 for CPU
                    compute_type = "float16" if device == "cuda" else "int8"

                self._model = WhisperModel(
                    self._model_name,
                    device=device,
                    compute_type=compute_type,
                )

                logger.info(f"Model loaded on {device} with {compute_type}")

            except ImportError as e:
                raise TranscriptionError(
                    "faster-whisper not installed. "
                    "Install with: pip install faster-whisper"
                ) from e
            except Exception as e:
                raise TranscriptionError(f"Failed to load faster-whisper model: {e}") from e

        return self._model

    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio file using faster-whisper.

        Args:
            audio_path: Path to audio file
            language: Language code ("auto" for auto-detection)

        Returns:
            TranscriptionResult with text and raw response

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_available():
            raise TranscriptionError(
                "faster-whisper not available. "
                "Install with: pip install faster-whisper"
            )

        try:
            model = self._get_model()

            logger.info(f"Transcribing with faster-whisper: {audio_path}")

            # transcribe() returns (segments_generator, info)
            segments, info = model.transcribe(
                audio_path,
                language=None if language == "auto" else language,
                beam_size=5,
                vad_filter=True,  # Filter out silence
            )

            # Collect all segment texts
            texts = []
            segments_list = []
            for segment in segments:
                texts.append(segment.text)
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                })

            text = " ".join(texts).strip()

            # Build raw response similar to OpenAI format
            raw_response = {
                "text": text,
                "segments": segments_list,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
            }

            return TranscriptionResult(
                text=text,
                raw_response=raw_response,
            )

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"faster-whisper transcription failed: {e}") from e

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Model unloaded")
