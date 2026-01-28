"""Centralized constants for SoupaWhisper.

This module contains all shared constants to avoid duplication (DRY principle).
"""

from pathlib import Path

# === Paths (DRY: single source of truth for all app directories) ===
# Base directories
CONFIG_DIR = Path.home() / ".config" / "soupawhisper"
CACHE_DIR = Path.home() / ".cache" / "soupawhisper"

# Config files
CONFIG_PATH = CONFIG_DIR / "config.ini"
PROVIDERS_PATH = CONFIG_DIR / "providers.json"
HISTORY_PATH = CONFIG_DIR / "history.md"
LOGS_DIR = CONFIG_DIR / "logs"

# Data directories
MODELS_DIR = CONFIG_DIR / "models"
DEBUG_DIR = CACHE_DIR / "debug"

# Lock file
LOCK_FILE = CACHE_DIR / "soupawhisper.lock"

# === Provider defaults ===
# Default transcription model
DEFAULT_MODEL = "whisper-large-v3"

# Default active provider
DEFAULT_PROVIDER = "groq"

# Groq API URL for transcription
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


# === Utility functions ===
def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating if necessary (DRY helper).

    Args:
        path: Directory path to create

    Returns:
        The same path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
