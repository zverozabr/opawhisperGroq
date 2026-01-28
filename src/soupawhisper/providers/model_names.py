"""Model name normalization helpers."""

from soupawhisper.providers.models import AVAILABLE_MODELS


class ModelNameResolver:
    """Resolves model names between short names and HF repos."""

    @staticmethod
    def extract_short_name(model_name: str) -> str:
        """Convert HF repo to short name.

        Examples:
            mlx-community/whisper-base-mlx -> base
            mlx-community/whisper-large-v3-turbo -> large-v3-turbo
        """
        if "/" not in model_name:
            return model_name
        name = model_name.split("/")[-1]
        name = name.replace("whisper-", "")
        if name.endswith("-mlx"):
            name = name[: -len("-mlx")]
        return name

    @staticmethod
    def to_mlx_repo(model_name: str) -> str:
        """Convert short name to MLX HF repo, if possible."""
        if "/" in model_name:
            return model_name
        info = AVAILABLE_MODELS.get(model_name)
        if info and info.mlx_repo:
            return info.mlx_repo
        return f"mlx-community/whisper-{model_name}-mlx"
