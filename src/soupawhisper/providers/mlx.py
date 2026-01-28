"""MLX-based local transcription provider for macOS Apple Silicon."""

import json
import logging
import subprocess
import sys
import time

from soupawhisper.providers.base import ProviderConfig, TranscriptionError, TranscriptionResult
from soupawhisper.providers.mlx_server_manager import (
    get_loaded_model,
    get_server_manager,
    is_server_running,
    shutdown_server,
    switch_model,
)
from soupawhisper.providers.model_names import ModelNameResolver

logger = logging.getLogger(__name__)

# Use persistent server for MLX to cache model in memory
# Falls back to subprocess per-request if server fails
USE_PERSISTENT_SERVER = True

# Re-export for backward compatibility
__all__ = [
    "MLXProvider",
    "shutdown_server",
    "get_loaded_model",
    "is_server_running",
    "switch_model",
]


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
        self._name_resolver = ModelNameResolver()
        model_name = self._config.model or self.DEFAULT_MODEL
        self._model_repo = self._name_resolver.to_mlx_repo(model_name)

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

    def _get_model_path(self) -> str:
        """Get model path - local if downloaded, otherwise HuggingFace repo.

        Returns:
            Local path if model is downloaded, otherwise HuggingFace repo ID.
        """
        try:
            from soupawhisper.providers.models import get_model_manager

            manager = get_model_manager()

            model_name = self._name_resolver.extract_short_name(self._model_repo)

            # Check if model is downloaded locally
            local_path = manager.get_model_path(model_name)
            if local_path and local_path.exists():
                logger.info(f"Using local model: {local_path}")
                return str(local_path)
        except Exception as e:
            logger.debug(f"Could not check local model: {e}")

        # Fallback to HuggingFace repo
        return self._model_repo

    def transcribe(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe audio file using local MLX Whisper.

        Uses persistent server process to cache model in memory.
        Falls back to subprocess per-request if server fails.

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

        if USE_PERSISTENT_SERVER:
            try:
                return self._transcribe_via_server(audio_path, language)
            except Exception as e:
                logger.warning(f"Server transcription failed, falling back to subprocess: {e}")
                return self._transcribe_subprocess(audio_path, language)
        else:
            return self._transcribe_subprocess(audio_path, language)

    def _ensure_server_running(self) -> subprocess.Popen:
        """Ensure the MLX server process is running.

        Returns:
            The server subprocess.
        """
        model_path = self._get_model_path()
        return get_server_manager().ensure_running(model_path)

    def _transcribe_via_server(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe using persistent server with cached model."""
        start_time = time.perf_counter()

        self._ensure_server_running()
        model_path = self._get_model_path()

        # Send request via server manager
        request = {
            "audio_path": audio_path,
            "language": language,
            "model": model_path,
        }
        response = get_server_manager().send_request(request)

        if "error" in response:
            raise TranscriptionError(f"Server error: {response['error']}")

        text = response.get("text", "")
        server_time_ms = response.get("time_ms", 0)
        total_ms = int((time.perf_counter() - start_time) * 1000)

        logger.debug(f"MLX server transcribe: {server_time_ms}ms, total: {total_ms}ms")

        return TranscriptionResult(
            text=text.strip(),
            raw_response=response,
        )

    def _transcribe_subprocess(self, audio_path: str, language: str) -> TranscriptionResult:
        """Transcribe using subprocess (fallback, no model caching)."""
        start_time = time.perf_counter()

        model_path = self._get_model_path()
        logger.info(f"Transcribing with MLX model (subprocess): {model_path}")

        lang_arg = "None" if language == "auto" else f'"{language}"'

        # Python script to run in subprocess - includes timing
        # condition_on_previous_text=False prevents hallucination loops
        script = f'''
import json
import time
import mlx_whisper

load_start = time.perf_counter()
result = mlx_whisper.transcribe(
    "{audio_path}",
    path_or_hf_repo="{model_path}",
    language={lang_arg},
    condition_on_previous_text=False,
)
load_end = time.perf_counter()
print(json.dumps({{"text": result.get("text", ""), "transcribe_ms": int((load_end - load_start) * 1000)}}))
'''

        try:
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise TranscriptionError(f"MLX subprocess failed: {result.stderr}")

            # Parse JSON output
            output = result.stdout.strip()
            # Find the JSON line (last line with valid JSON)
            for line in reversed(output.split("\n")):
                if line.startswith("{"):
                    data = json.loads(line)
                    text = data.get("text", "")
                    transcribe_ms = data.get("transcribe_ms", 0)
                    total_ms = int((time.perf_counter() - start_time) * 1000)
                    logger.debug(f"MLX transcribe: {transcribe_ms}ms, subprocess total: {total_ms}ms")
                    return TranscriptionResult(
                        text=text.strip(),
                        raw_response=data,
                    )

            raise TranscriptionError(f"No JSON output from MLX: {output[:200]}")

        except subprocess.TimeoutExpired:
            raise TranscriptionError("MLX transcription timed out (120s)")
        except json.JSONDecodeError as e:
            raise TranscriptionError(f"Failed to parse MLX output: {e}")
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"MLX subprocess error: {e}")
