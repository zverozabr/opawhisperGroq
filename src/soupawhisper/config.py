"""Configuration management."""

import configparser
from dataclasses import dataclass
from pathlib import Path

from .constants import DEFAULT_MODEL, DEFAULT_PROVIDER

CONFIG_PATH = Path.home() / ".config" / "soupawhisper" / "config.ini"

# Valid option values
VALID_LANGUAGES = {"auto", "ru", "en", "de", "fr", "es", "zh", "ja", "ko", "pt", "it", "nl", "pl", "uk"}
VALID_BACKENDS = {"auto", "x11", "wayland", "darwin", "windows"}


def get_valid_hotkeys() -> set[str]:
    """Get set of valid hotkey names from pynput mapping.

    Returns:
        Set of valid hotkey strings (e.g., 'ctrl_r', 'f12')
    """
    try:
        from soupawhisper.backend.keys import PYNPUT_KEY_TO_NAME

        return set(PYNPUT_KEY_TO_NAME.values())
    except ImportError:
        # Fallback if pynput not available
        return {"ctrl_r", "ctrl_l", "alt_r", "f12", "f11", "f10", "f9"}


# Valid modifiers for combo hotkeys
VALID_MODIFIERS = {"ctrl", "alt", "shift", "super"}

# Valid keys for combos (letters and digits)
COMBO_KEYS = set("qwertyuiopasdfghjklzxcvbnm1234567890")


def is_valid_hotkey(hotkey: str) -> bool:
    """Check if hotkey string is valid.

    Supports:
    - Single keys: f9, ctrl_r, space
    - Combos: ctrl+g, alt+f9, shift+space

    Args:
        hotkey: Hotkey string to validate

    Returns:
        True if valid, False otherwise
    """
    valid_singles = get_valid_hotkeys()

    # Check if it's a valid single key
    if hotkey in valid_singles:
        return True

    # Check if it's a valid combo (modifier+key)
    if "+" in hotkey:
        parts = hotkey.split("+", 1)
        if len(parts) == 2:
            modifier, key = parts
            # Modifier must be valid
            if modifier not in VALID_MODIFIERS:
                return False
            # Key can be a letter/digit or a valid single key
            if key in COMBO_KEYS or key in valid_singles:
                return True

    return False


@dataclass
class Config:
    """Application configuration."""

    api_key: str
    model: str = DEFAULT_MODEL
    language: str = "auto"  # "auto" for auto-detect, or language code like "ru", "en"
    hotkey: str = "ctrl_r"
    auto_type: bool = True
    auto_enter: bool = False  # Press Enter after typing
    typing_delay: int = 12  # Delay between keystrokes in ms (0 = fastest, 12 = default)
    notifications: bool = True
    backend: str = "auto"  # "auto", "x11", "wayland", "darwin"
    audio_device: str = "default"  # Microphone device ID
    history_enabled: bool = True  # Save transcription history
    history_days: int = 3  # Keep history for N days
    debug: bool = False  # Save last 3 recordings for debugging
    active_provider: str = DEFAULT_PROVIDER  # Active transcription provider name

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load configuration from file."""
        parser = configparser.ConfigParser()

        if path.exists():
            parser.read(path)

        return cls(
            api_key=parser.get("groq", "api_key", fallback=""),
            model=parser.get("groq", "model", fallback=DEFAULT_MODEL),
            language=parser.get("groq", "language", fallback="auto"),
            hotkey=parser.get("hotkey", "key", fallback="ctrl_r"),
            auto_type=parser.getboolean("behavior", "auto_type", fallback=True),
            auto_enter=parser.getboolean("behavior", "auto_enter", fallback=False),
            typing_delay=parser.getint("behavior", "typing_delay", fallback=12),
            notifications=parser.getboolean("behavior", "notifications", fallback=True),
            backend=parser.get("behavior", "backend", fallback="auto"),
            audio_device=parser.get("audio", "device", fallback="default"),
            history_enabled=parser.getboolean("history", "enabled", fallback=True),
            history_days=parser.getint("history", "days", fallback=3),
            debug=parser.getboolean("behavior", "debug", fallback=False),
            active_provider=parser.get("provider", "active", fallback=DEFAULT_PROVIDER),
        )

    def save(self, path: Path = CONFIG_PATH) -> None:
        """Save configuration to file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        parser = configparser.ConfigParser()
        parser["groq"] = {
            "api_key": self.api_key,
            "model": self.model,
            "language": self.language,
        }
        parser["hotkey"] = {"key": self.hotkey}
        parser["behavior"] = {
            "auto_type": str(self.auto_type).lower(),
            "auto_enter": str(self.auto_enter).lower(),
            "typing_delay": str(self.typing_delay),
            "notifications": str(self.notifications).lower(),
            "backend": self.backend,
            "debug": str(self.debug).lower(),
        }
        parser["audio"] = {"device": self.audio_device}
        parser["history"] = {
            "enabled": str(self.history_enabled).lower(),
            "days": str(self.history_days),
        }
        parser["provider"] = {"active": self.active_provider}

        with open(path, "w") as f:
            parser.write(f)

    def validate(self) -> list[str]:
        """Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate language
        if self.language not in VALID_LANGUAGES:
            errors.append(f"Invalid language '{self.language}'. Valid: {', '.join(sorted(VALID_LANGUAGES))}")

        # Validate hotkey
        if not is_valid_hotkey(self.hotkey):
            errors.append(f"Invalid hotkey '{self.hotkey}'. Use single key (f9, ctrl_r) or combo (ctrl+g)")

        # Validate backend
        if self.backend not in VALID_BACKENDS:
            errors.append(f"Invalid backend '{self.backend}'. Valid: {', '.join(sorted(VALID_BACKENDS))}")

        # Validate typing_delay
        if self.typing_delay < 0 or self.typing_delay > 1000:
            errors.append(f"typing_delay must be 0-1000ms, got {self.typing_delay}")

        # Validate history_days
        if self.history_days < 1 or self.history_days > 365:
            errors.append(f"history_days must be 1-365, got {self.history_days}")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
