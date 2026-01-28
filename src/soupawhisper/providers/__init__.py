"""Transcription providers registry.

Manages multiple transcription providers with JSON configuration.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

from soupawhisper.constants import DEFAULT_MODEL, DEFAULT_PROVIDER, GROQ_API_URL
from soupawhisper.providers.base import (
    ProviderConfig,
    TranscriptionError,
    TranscriptionProvider,
    TranscriptionResult,
)
from soupawhisper.providers.faster_whisper import FasterWhisperProvider
from soupawhisper.providers.mlx import MLXProvider
from soupawhisper.providers.openai_compatible import OpenAICompatibleProvider

__all__ = [
    "TranscriptionProvider",
    "TranscriptionResult",
    "TranscriptionError",
    "ProviderConfig",
    "OpenAICompatibleProvider",
    "MLXProvider",
    "FasterWhisperProvider",
    "get_provider",
    "get_best_local_provider",
    "list_providers",
    "list_available_local_providers",
    "get_active_provider_name",
    "set_active_provider",
    "load_providers_config",
    "save_providers_config",
    "migrate_from_config_ini",
]

logger = logging.getLogger(__name__)

PROVIDERS_PATH = Path.home() / ".config" / "soupawhisper" / "providers.json"

# Default provider configurations
DEFAULT_PROVIDERS: dict[str, dict[str, Any]] = {
    DEFAULT_PROVIDER: {
        "type": "openai_compatible",
        "url": GROQ_API_URL,
        "api_key": "",
        "model": DEFAULT_MODEL,
    },
    "local-mlx": {
        "type": "mlx",
        "model": "mlx-community/whisper-large-v3-turbo",
    },
    "local-cpu": {
        "type": "faster_whisper",
        "model": "large-v3-turbo",
        "device": "cpu",
    },
}


def load_providers_config() -> dict[str, Any]:
    """Load providers configuration from JSON file.

    Returns:
        Dict with 'active' and 'providers' keys
    """
    if not PROVIDERS_PATH.exists():
        return {"active": DEFAULT_PROVIDER, "providers": {}}

    try:
        with open(PROVIDERS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load providers.json: {e}")
        return {"active": DEFAULT_PROVIDER, "providers": {}}


def save_providers_config(config: dict[str, Any]) -> None:
    """Save providers configuration to JSON file.

    Args:
        config: Dict with 'active' and 'providers' keys
    """
    PROVIDERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(PROVIDERS_PATH, "w") as f:
        json.dump(config, f, indent=2)


def migrate_from_config_ini() -> bool:
    """Migrate from old config.ini [groq] section to providers.json.

    Returns:
        True if migration was performed, False if not needed
    """
    if PROVIDERS_PATH.exists():
        # Already have providers.json
        config = load_providers_config()
        if config.get("providers"):
            return False

    # Try to load from old config.ini
    try:
        from soupawhisper.config import CONFIG_PATH

        if not CONFIG_PATH.exists():
            return False

        import configparser

        parser = configparser.ConfigParser()
        parser.read(CONFIG_PATH)

        api_key = parser.get("groq", "api_key", fallback="")
        model = parser.get("groq", "model", fallback=DEFAULT_MODEL)

        if not api_key:
            return False

        # Create providers.json with migrated settings
        providers_config = {
            "active": DEFAULT_PROVIDER,
            "providers": {
                DEFAULT_PROVIDER: {
                    "type": "openai_compatible",
                    "url": GROQ_API_URL,
                    "api_key": api_key,
                    "model": model,
                },
            },
        }

        save_providers_config(providers_config)
        logger.info("Migrated Groq settings from config.ini to providers.json")
        return True

    except Exception as e:
        logger.warning(f"Failed to migrate from config.ini: {e}")
        return False


def list_providers() -> list[str]:
    """Get list of configured provider names.

    Returns:
        List of provider names
    """
    config = load_providers_config()
    return list(config.get("providers", {}).keys())


def get_active_provider_name() -> str:
    """Get name of the currently active provider.

    Returns:
        Active provider name
    """
    config = load_providers_config()
    return config.get("active", DEFAULT_PROVIDER)


def set_active_provider(name: str) -> None:
    """Set the active provider by name.

    Args:
        name: Provider name to activate

    Raises:
        ValueError: If provider doesn't exist
    """
    config = load_providers_config()

    if name not in config.get("providers", {}):
        available = list(config.get("providers", {}).keys())
        raise ValueError(f"Provider '{name}' not found. Available: {available}")

    config["active"] = name
    save_providers_config(config)


def _create_provider(config: ProviderConfig) -> TranscriptionProvider:
    """Create provider instance from config.

    Args:
        config: Provider configuration

    Returns:
        Provider instance

    Raises:
        ValueError: If provider type is unknown
    """
    if config.type == "openai_compatible":
        return OpenAICompatibleProvider(config)
    elif config.type == "mlx":
        return MLXProvider(config)
    elif config.type == "faster_whisper":
        return FasterWhisperProvider(config)
    else:
        raise ValueError(f"Unknown provider type: {config.type}")


def list_available_local_providers() -> list[str]:
    """Get list of available local provider types for current platform.

    Returns:
        List of provider type names that can be used locally
    """
    available = []

    # Check MLX (macOS only)
    if sys.platform == "darwin":
        try:
            import mlx_whisper  # noqa: F401

            available.append("mlx")
        except ImportError:
            pass

    # Check faster-whisper (cross-platform)
    try:
        import faster_whisper  # noqa: F401

        available.append("faster_whisper")
    except ImportError:
        pass

    return available


def get_best_local_provider() -> str | None:
    """Auto-detect best local provider for current platform.

    Returns:
        Provider type name, or None if no local providers available
    """
    available = list_available_local_providers()

    if not available:
        return None

    # Prefer MLX on macOS (optimized for Apple Silicon)
    if "mlx" in available:
        return "mlx"

    # Fall back to faster-whisper
    if "faster_whisper" in available:
        return "faster_whisper"

    return None


def ensure_default_local_provider() -> str | None:
    """Ensure a local provider is configured if available.

    Creates a default local provider config if one doesn't exist.

    Returns:
        Name of the local provider, or None if not available
    """
    best = get_best_local_provider()
    if not best:
        return None

    config = load_providers_config()
    providers = config.get("providers", {})

    # Check if we already have a local provider
    for name, data in providers.items():
        if data.get("type") in ("mlx", "faster_whisper"):
            return name

    # Create default local provider
    if best == "mlx":
        provider_name = "local-mlx"
        provider_data = {
            "type": "mlx",
            "model": "mlx-community/whisper-large-v3-turbo",
        }
    else:
        provider_name = "local-cpu"
        provider_data = {
            "type": "faster_whisper",
            "model": "large-v3-turbo",
            "device": "auto",
        }

    if "providers" not in config:
        config["providers"] = {}

    config["providers"][provider_name] = provider_data
    save_providers_config(config)

    logger.info(f"Created default local provider: {provider_name}")
    return provider_name


def get_provider(name: str | None = None) -> TranscriptionProvider:
    """Get provider instance by name.

    Args:
        name: Provider name, or None to get active provider

    Returns:
        TranscriptionProvider instance

    Raises:
        ValueError: If provider not found or not configured
    """
    # Try migration if needed
    migrate_from_config_ini()

    config = load_providers_config()
    providers = config.get("providers", {})

    if name is None:
        name = config.get("active", DEFAULT_PROVIDER)

    if name not in providers:
        # Check if we have any providers at all
        if not providers:
            raise ValueError(
                "No providers configured. Add a provider to "
                f"{PROVIDERS_PATH} or set API key in GUI."
            )
        raise ValueError(f"Provider '{name}' not found. Available: {list(providers.keys())}")

    provider_data = providers[name]
    provider_config = ProviderConfig.from_dict(name, provider_data)

    return _create_provider(provider_config)


def add_provider(
    name: str,
    provider_type: str,
    url: str | None = None,
    api_key: str | None = None,
    model: str = "whisper-large-v3",
) -> None:
    """Add a new provider configuration.

    Args:
        name: Unique provider name
        provider_type: Provider type ("openai_compatible" or "mlx")
        url: API URL (for openai_compatible)
        api_key: API key (for openai_compatible)
        model: Model name
    """
    config = load_providers_config()

    provider_data: dict[str, Any] = {"type": provider_type, "model": model}
    if url:
        provider_data["url"] = url
    if api_key:
        provider_data["api_key"] = api_key

    if "providers" not in config:
        config["providers"] = {}

    config["providers"][name] = provider_data
    save_providers_config(config)


def remove_provider(name: str) -> None:
    """Remove a provider configuration.

    Args:
        name: Provider name to remove

    Raises:
        ValueError: If provider doesn't exist or is the active one
    """
    config = load_providers_config()

    if name not in config.get("providers", {}):
        raise ValueError(f"Provider '{name}' not found")

    if config.get("active") == name:
        raise ValueError(f"Cannot remove active provider '{name}'. Switch to another first.")

    del config["providers"][name]
    save_providers_config(config)


def update_provider_api_key(name: str, api_key: str) -> None:
    """Update API key for a provider.

    Args:
        name: Provider name
        api_key: New API key
    """
    config = load_providers_config()

    if name not in config.get("providers", {}):
        raise ValueError(f"Provider '{name}' not found")

    config["providers"][name]["api_key"] = api_key
    save_providers_config(config)
