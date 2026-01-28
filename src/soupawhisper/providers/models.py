"""Model manager for local transcription providers.

Handles downloading, caching, and managing Whisper models.
"""

import logging
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from soupawhisper.constants import MODELS_DIR, ensure_dir

if TYPE_CHECKING:
    from soupawhisper.providers.model_preloader import ModelPreloader

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Status of a local model."""

    NOT_DOWNLOADED = "not_downloaded"  # Model not on disk
    DOWNLOADED = "downloaded"  # On disk but not in memory
    LOADING = "loading"  # Currently loading into memory
    LOADED = "loaded"  # In memory, ready for instant use


class ModelNotDownloadedError(Exception):
    """Raised when trying to preload a model that's not downloaded."""

    pass


class ModelStatusFormatter:
    """Format model status for display."""

    @staticmethod
    def format_status(
        status: ModelStatus, model_name: str, manager: "ModelManager"
    ) -> str:
        if status == ModelStatus.LOADED:
            disk_mb = manager.get_size_on_disk(model_name) // (1024 * 1024)
            return f"Loaded in memory ({disk_mb} MB)"
        if status == ModelStatus.LOADING:
            return "Loading into memory..."
        if status == ModelStatus.DOWNLOADED:
            disk_mb = manager.get_size_on_disk(model_name) // (1024 * 1024)
            return f"Downloaded ({disk_mb} MB)"
        return "Not downloaded"


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


@dataclass
class DownloadProgress:
    """Progress information for model download."""

    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_mbps: float = 0.0
    eta_seconds: float = 0.0
    percent: float = 0.0

    def __post_init__(self):
        if self.total_bytes > 0:
            self.percent = (self.downloaded_bytes / self.total_bytes) * 100


@dataclass
class DownloadResult:
    """Result of model download with metrics."""

    model_name: str
    path: Path
    size_bytes: int
    download_time_seconds: float
    avg_speed_mbps: float = field(init=False)

    def __post_init__(self):
        if self.download_time_seconds > 0:
            self.avg_speed_mbps = (self.size_bytes / 1024 / 1024) / self.download_time_seconds
        else:
            self.avg_speed_mbps = 0.0


# Available multilingual models with metadata
# Based on official OpenAI Whisper: https://github.com/openai/whisper
# Ordered by size/speed: tiny < base < small < medium < large < turbo
AVAILABLE_MODELS: dict[str, ModelInfo] = {
    "tiny": ModelInfo(
        name="tiny",
        size_mb=74,
        description="39M params, ~1GB VRAM, fastest",
        mlx_repo="mlx-community/whisper-tiny-mlx",
        faster_whisper_name="tiny",
    ),
    "base": ModelInfo(
        name="base",
        size_mb=142,
        description="74M params, ~1GB VRAM, fast",
        mlx_repo="mlx-community/whisper-base-mlx",
        faster_whisper_name="base",
    ),
    "small": ModelInfo(
        name="small",
        size_mb=466,
        description="244M params, ~2GB VRAM, balanced",
        mlx_repo="mlx-community/whisper-small-mlx",
        faster_whisper_name="small",
    ),
    "medium": ModelInfo(
        name="medium",
        size_mb=1500,
        description="769M params, ~5GB VRAM, accurate",
        mlx_repo="mlx-community/whisper-medium-mlx",
        faster_whisper_name="medium",
    ),
    "large": ModelInfo(
        name="large",
        size_mb=2900,
        description="1550M params, ~10GB VRAM, v1",
        mlx_repo="mlx-community/whisper-large-mlx",
        faster_whisper_name="large",
    ),
    "large-v3": ModelInfo(
        name="large-v3",
        size_mb=3100,
        description="1550M params, ~10GB VRAM, best accuracy",
        mlx_repo="mlx-community/whisper-large-v3-mlx",
        faster_whisper_name="large-v3",
    ),
    "turbo": ModelInfo(
        name="turbo",
        size_mb=1600,
        description="809M params, ~6GB VRAM, optimized large-v3",
        mlx_repo="mlx-community/whisper-turbo",
        faster_whisper_name="turbo",
    ),
}

# Progress callback type: (progress: DownloadProgress) -> None
ProgressCallback = Callable[["DownloadProgress"], None]


class ModelManager:
    """Manages downloading and caching of Whisper models."""

    def __init__(
        self,
        models_dir: Path | None = None,
        preloader: "ModelPreloader | None" = None,
    ) -> None:
        """Initialize model manager.

        Args:
            models_dir: Directory to store models. Defaults to ~/.config/soupawhisper/models/
        """
        self._models_dir = models_dir or MODELS_DIR
        ensure_dir(self._models_dir)
        if preloader is None:
            from soupawhisper.providers.model_preloader import ModelPreloader

            self._preloader = ModelPreloader(self)
        else:
            self._preloader = preloader

    @property
    def models_dir(self) -> Path:
        """Get models directory path."""
        return self._models_dir

    def list_available(self) -> list[ModelInfo]:
        """Get list of available models to download.

        Returns:
            List of ModelInfo objects (multilingual only)
        """
        return list(AVAILABLE_MODELS.values())

    def list_multilingual(self) -> list[ModelInfo]:
        """Get list of multilingual models (no .en suffix).

        Returns:
            List of ModelInfo objects for multilingual models
        """
        return [m for m in AVAILABLE_MODELS.values() if ".en" not in m.name]

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
        progress_callback: Optional[ProgressCallback] = None,
    ) -> DownloadResult:
        """Download model for MLX provider (uses HuggingFace Hub).

        Args:
            model_name: Model name (e.g., "large-v3", "turbo")
            progress_callback: Optional callback for download progress

        Returns:
            DownloadResult with path and metrics

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
            start_time = time.time()

            # Track progress via tqdm callback
            class ProgressTracker:
                def __init__(self, callback: Optional[ProgressCallback]):
                    self.callback = callback
                    self.downloaded = 0
                    self.total = model_info.size_mb * 1024 * 1024  # Estimate
                    self.start_time = time.time()

                def __call__(self, n_bytes: int):
                    self.downloaded += n_bytes
                    if self.callback:
                        elapsed = time.time() - self.start_time
                        speed = (self.downloaded / 1024 / 1024) / elapsed if elapsed > 0 else 0
                        remaining = self.total - self.downloaded
                        eta = remaining / (self.downloaded / elapsed) if self.downloaded > 0 else 0
                        progress = DownloadProgress(
                            downloaded_bytes=self.downloaded,
                            total_bytes=self.total,
                            speed_mbps=speed,
                            eta_seconds=eta,
                        )
                        self.callback(progress)

            # HuggingFace Hub handles caching and progress
            snapshot_download(
                repo_id=model_info.mlx_repo,
                local_dir=str(model_path),
            )

            download_time = time.time() - start_time
            size_on_disk = self.get_size_on_disk(model_name)

            logger.info(
                f"Model {model_name} downloaded to {model_path} "
                f"({size_on_disk / 1024 / 1024:.1f} MB in {download_time:.1f}s)"
            )

            # Final progress callback
            if progress_callback:
                progress_callback(DownloadProgress(
                    downloaded_bytes=size_on_disk,
                    total_bytes=size_on_disk,
                    speed_mbps=size_on_disk / 1024 / 1024 / download_time if download_time > 0 else 0,
                    eta_seconds=0,
                ))

            return DownloadResult(
                model_name=model_name,
                path=model_path,
                size_bytes=size_on_disk,
                download_time_seconds=download_time,
            )

        except ImportError:
            raise RuntimeError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download model {model_name}: {e}") from e

    def download_for_faster_whisper(
        self,
        model_name: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> DownloadResult:
        """Download/prepare model for faster-whisper.

        faster-whisper downloads models automatically on first use,
        but we can pre-download to the cache.

        Args:
            model_name: Model name (e.g., "large-v3", "turbo")
            progress_callback: Optional callback for download progress

        Returns:
            DownloadResult with metrics

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
            start_time = time.time()

            # Notify start
            if progress_callback:
                progress_callback(DownloadProgress(
                    downloaded_bytes=0,
                    total_bytes=model_info.size_mb * 1024 * 1024,
                    speed_mbps=0,
                    eta_seconds=0,
                ))

            # This will download the model if not cached
            # faster-whisper manages its own cache in ~/.cache/huggingface/
            WhisperModel(
                model_info.faster_whisper_name,
                device="cpu",  # Just for download, don't need GPU
                compute_type="int8",
            )

            download_time = time.time() - start_time
            estimated_size = model_info.size_mb * 1024 * 1024

            logger.info(
                f"Model {model_name} ready for faster-whisper "
                f"(~{model_info.size_mb} MB in {download_time:.1f}s)"
            )

            # Final progress callback
            if progress_callback:
                progress_callback(DownloadProgress(
                    downloaded_bytes=estimated_size,
                    total_bytes=estimated_size,
                    speed_mbps=model_info.size_mb / download_time if download_time > 0 else 0,
                    eta_seconds=0,
                ))

            # faster-whisper uses its own cache, return estimated size
            return DownloadResult(
                model_name=model_name,
                path=Path.home() / ".cache" / "huggingface" / "hub",
                size_bytes=estimated_size,
                download_time_seconds=download_time,
            )

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

    def list_models(self) -> list[ModelInfo]:
        """Get list of all available models.

        Returns:
            List of ModelInfo objects
        """
        return list(AVAILABLE_MODELS.values())

    def get_model_status(self, model_name: str) -> ModelStatus:
        """Get current status of a model.

        Args:
            model_name: Model name

        Returns:
            ModelStatus enum value
        """
        # Check if downloaded
        if not self.is_downloaded(model_name):
            return ModelStatus.NOT_DOWNLOADED

        # Check if loaded in server
        try:
            from soupawhisper.providers.mlx import get_loaded_model

            loaded_model = get_loaded_model()
            if loaded_model:
                # Check if this model is the loaded one
                model_path = self._models_dir / model_name
                if str(model_path) == loaded_model or model_name in loaded_model:
                    return ModelStatus.LOADED
        except ImportError:
            pass

        return ModelStatus.DOWNLOADED

    def preload_model(self, model_name: str, provider_type: str = "mlx") -> None:
        """Preload a model into memory for instant use.

        Args:
            model_name: Model name to preload
            provider_type: Provider type for preloading (default: "mlx")

        Raises:
            ModelNotDownloadedError: If model is not downloaded
        """
        self._preloader.preload(model_name, provider_type=provider_type)

    def unload_model(self, provider_type: str = "mlx") -> None:
        """Unload the currently loaded model from memory.

        This stops the provider backend and frees memory.
        """
        self._preloader.unload(provider_type=provider_type)


# Singleton instance
_manager: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """Get singleton ModelManager instance."""
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
