"""Configuration management."""

import configparser
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "soupawhisper" / "config.ini"


@dataclass
class Config:
    """Application configuration."""

    api_key: str
    model: str = "whisper-large-v3"
    language: str = "auto"  # "auto" for auto-detect, or language code like "ru", "en"
    hotkey: str = "ctrl_r"
    auto_type: bool = True
    auto_enter: bool = False  # Press Enter after typing
    typing_delay: int = 12  # Delay between keystrokes in ms (0 = fastest, 12 = default)
    notifications: bool = True
    backend: str = "auto"  # "auto", "x11", "wayland", "darwin"

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load configuration from file."""
        parser = configparser.ConfigParser()

        if path.exists():
            parser.read(path)

        return cls(
            api_key=parser.get("groq", "api_key", fallback=""),
            model=parser.get("groq", "model", fallback="whisper-large-v3"),
            language=parser.get("groq", "language", fallback="auto"),
            hotkey=parser.get("hotkey", "key", fallback="ctrl_r"),
            auto_type=parser.getboolean("behavior", "auto_type", fallback=True),
            auto_enter=parser.getboolean("behavior", "auto_enter", fallback=False),
            typing_delay=parser.getint("behavior", "typing_delay", fallback=12),
            notifications=parser.getboolean("behavior", "notifications", fallback=True),
            backend=parser.get("behavior", "backend", fallback="auto"),
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
        }

        with open(path, "w") as f:
            parser.write(f)
