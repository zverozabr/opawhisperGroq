"""Model manager for local transcription providers.

Handles downloading, caching, and managing Whisper models.
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# Default models directory
MODELS_DIR = Path.home() / ".config" / "soupawhisper" / "models"


@dataclass
class ModelInfo:
    """Information about a Whisper model."""

    name: str
    size_mb: int
    description: str
    # HuggingFace repo for MLX models
    mlx_repo: str | None = None
    # Model name for faster-whisper
    faster_whisper_name: str | None = None


# Available models with metadata
AVAILABLE_MODELS: dict[str, ModelInfo] = {
    "tiny": ModelInfo(
        name="tiny",
        size_mb=74,
        description="Fastest, lowest accuracy",
        mlx_repo="mlx-community/whisper-tiny-mlx",
        faster_whisper_name="tiny",
    ),
    "base": ModelInfo(
        name="base",
        size_mb=142,
        description="Fast, basic accuracy",
        mlx_repo="mlx-community/whisper-base-mlx",
        faster_whisper_name="base",
    ),
    "small": ModelInfo(
        name="small",
        size_mb=466,
        description="Balanced speed/accuracy",
        mlx_repo="mlx-community/whisper-small-mlx",
        faster_whisper_name="small",
    ),
    "medium": ModelInfo(
        name="medium",
        size_mb=1500,
        description="Good accuracy, slower",
        mlx_repo="mlx-community/whisper-medium-mlx",
        faster_whisper_name="medium",
    ),
    "large-v3": ModelInfo(
        name="large-v3",
        size_mb=3100,
        description="Best accuracy, slowest",
        mlx_repo="mlx-community/whisper-large-v3-mlx",
        faster_whisper_name="large-v3",
    ),
    "large-v3-turbo": ModelInfo(
        name="large-v3-turbo",
        size_mb=1600,
        description="Good accuracy, faster than large",
        mlx_repo="mlx-community/whisper-large-v3-turbo",
        faster_whisper_name="large-v3-turbo",
    ),
}

# Progress callback type: (downloaded_bytes, total_bytes) -> None
ProgressCallback = Callable[[int, int], None]


class ModelManager:
    """Manages downloading and caching of Whisper models."""

    def __init__(self, models_dir: Path | None = None) -> None:
        """Initialize model manager.

        Args:
            models_dir: Directory to store models. Defaults to ~/.config/soupawhisper/models/
        """
        self._models_dir = models_dir or MODELS_DIR
        self._models_dir.mkdir(parents=True, exist_ok=True)

    @property
    def models_dir(self) -> Path:
        """Get models directory path."""
        return self._models_dir

    def list_available(self) -> list[ModelInfo]:
        """Get list of available models to download.

        Returns:
            List of ModelInfo objects
        """
        return list(AVAILABLE_MODELS.values())

    def list_downloaded(self) -> list[str]:
        """Get list of downloaded model names.

        Returns:
            List of model names that are downloaded locally
        """
        downloaded = []
        for name in AVAILABLE_MODELS:
            if self.is_downloaded(name):
                downloaded.append(name)
        return downloaded

    def is_downloaded(self, model_name: str) -> bool:
        """Check if a model is downloaded.

        Args:
            model_name: Model name (e.g., "large-v3-turbo")

        Returns:
            True if model is available locally
        """
        model_path = self._models_dir / model_name
        if model_path.exists() and model_path.is_dir():
            # Check if it has actual model files
            return any(model_path.iterdir())
        return False

    def get_model_path(self, model_name: str) -> Path | None:
        """Get path to downloaded model.

        Args:
            model_name: Model name

        Returns:
            Path to model directory, or None if not downloaded
        """
        if self.is_downloaded(model_name):
            return self._models_dir / model_name
        return None

    def get_model_info(self, model_name: str) -> ModelInfo | None:
        """Get model metadata.

        Args:
            model_name: Model name

        Returns:
            ModelInfo or None if model not found
        """
        return AVAILABLE_MODELS.get(model_name)

    def download_for_mlx(
        self,
        model_name: str,
        progress_callback: ProgressCallback | None = None,
    ) -> Path:
        """Download model for MLX provider (uses HuggingFace Hub).

        Args:
            model_name: Model name (e.g., "large-v3-turbo")
            progress_callback: Optional callback for download progress

        Returns:
            Path to downloaded model

        Raises:
            ValueError: If model not found
            RuntimeError: If download fails
        """
        model_info = AVAILABLE_MODELS.get(model_name)
        if not model_info or not model_info.mlx_repo:
            raise ValueError(f"Unknown MLX model: {model_name}")

        try:
            from huggingface_hub import snapshot_download

            logger.info(f"Downloading MLX model {model_name} from {model_info.mlx_repo}")

            # Download to models directory
            model_path = self._models_dir / model_name

            # HuggingFace Hub handles caching and progress
            snapshot_download(
                repo_id=model_info.mlx_repo,
                local_dir=str(model_path),
                local_dir_use_symlinks=False,
            )

            logger.info(f"Model {model_name} downloaded to {model_path}")
            return model_path

        except ImportError:
            raise RuntimeError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download model {model_name}: {e}") from e

    def download_for_faster_whisper(
        self,
        model_name: str,
        progress_callback: ProgressCallback | None = None,
    ) -> str:
        """Download/prepare model for faster-whisper.

        faster-whisper downloads models automatically on first use,
        but we can pre-download to the cache.

        Args:
            model_name: Model name (e.g., "large-v3-turbo")
            progress_callback: Optional callback for download progress

        Returns:
            Model name (faster-whisper uses its own cache)

        Raises:
            ValueError: If model not found
            RuntimeError: If download fails
        """
        model_info = AVAILABLE_MODELS.get(model_name)
        if not model_info or not model_info.faster_whisper_name:
            raise ValueError(f"Unknown faster-whisper model: {model_name}")

        try:
            from faster_whisper import WhisperModel

            logger.info(f"Pre-downloading faster-whisper model: {model_name}")

            # This will download the model if not cached
            # faster-whisper manages its own cache in ~/.cache/huggingface/
            WhisperModel(
                model_info.faster_whisper_name,
                device="cpu",  # Just for download, don't need GPU
                compute_type="int8",
            )

            logger.info(f"Model {model_name} ready for faster-whisper")
            return model_info.faster_whisper_name

        except ImportError:
            raise RuntimeError(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download model {model_name}: {e}") from e

    def delete(self, model_name: str) -> bool:
        """Delete a downloaded model.

        Args:
            model_name: Model name to delete

        Returns:
            True if deleted, False if not found
        """
        model_path = self._models_dir / model_name
        if model_path.exists():
            shutil.rmtree(model_path)
            logger.info(f"Deleted model: {model_name}")
            return True
        return False

    def get_size_on_disk(self, model_name: str) -> int:
        """Get size of downloaded model in bytes.

        Args:
            model_name: Model name

        Returns:
            Size in bytes, or 0 if not downloaded
        """
        model_path = self._models_dir / model_name
        if not model_path.exists():
            return 0

        total = 0
        for f in model_path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total


# Singleton instance
_manager: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """Get singleton ModelManager instance."""
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
