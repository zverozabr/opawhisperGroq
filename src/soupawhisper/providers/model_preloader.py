"""Preload and unload local models into memory."""

from typing import Optional, Protocol

from soupawhisper.providers.base import ProviderConfig
from soupawhisper.providers.mlx import MLXProvider, get_loaded_model, switch_model
from soupawhisper.providers.models import ModelNotDownloadedError, ModelManager


class ModelLoader(Protocol):
    """Provider-specific model loader."""

    def preload(self, model_name: str) -> None:
        """Preload a model into memory."""

    def unload(self) -> None:
        """Unload the model from memory."""

    def get_loaded_model(self) -> Optional[str]:
        """Return the loaded model path, or None."""


class MLXModelLoader:
    """MLX model loader implementation."""

    def __init__(self, model_manager: ModelManager) -> None:
        self._manager = model_manager

    def preload(self, model_name: str) -> None:
        if not self._manager.is_downloaded(model_name):
            raise ModelNotDownloadedError(
                f"Model '{model_name}' is not downloaded. "
                "Download it first before preloading."
            )

        model_path = self._manager.get_model_path(model_name)
        if model_path is None:
            raise ModelNotDownloadedError(
                f"Model '{model_name}' is not downloaded. "
                "Download it first before preloading."
            )

        model_path_str = str(model_path)
        current_model = get_loaded_model()
        if current_model and current_model != model_path_str:
            switch_model(model_path_str)

        config = ProviderConfig(
            name="preload",
            type="mlx",
            model=model_name,
        )
        provider = MLXProvider(config)
        provider._ensure_server_running()

    def unload(self) -> None:
        from soupawhisper.providers.mlx import shutdown_server

        shutdown_server()

    def get_loaded_model(self) -> Optional[str]:
        return get_loaded_model()


class ModelPreloader:
    """Coordinates preloading across provider types."""

    def __init__(
        self,
        model_manager: ModelManager,
        loaders: Optional[dict[str, ModelLoader]] = None,
    ) -> None:
        self._model_manager = model_manager
        self._loaders = loaders or {"mlx": MLXModelLoader(model_manager)}

    def register_loader(self, provider_type: str, loader: ModelLoader) -> None:
        self._loaders[provider_type] = loader

    def preload(self, model_name: str, provider_type: str = "mlx") -> None:
        loader = self._loaders.get(provider_type)
        if loader is None:
            raise ValueError(f"No loader registered for provider type: {provider_type}")
        loader.preload(model_name)

    def unload(self, provider_type: str = "mlx") -> None:
        loader = self._loaders.get(provider_type)
        if loader is None:
            raise ValueError(f"No loader registered for provider type: {provider_type}")
        loader.unload()
