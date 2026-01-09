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
    language: str = "ru"
    hotkey: str = "ctrl_r"
    auto_type: bool = True
    notifications: bool = True

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load configuration from file."""
        parser = configparser.ConfigParser()

        if path.exists():
            parser.read(path)

        return cls(
            api_key=parser.get("groq", "api_key", fallback=""),
            model=parser.get("groq", "model", fallback="whisper-large-v3"),
            language=parser.get("groq", "language", fallback="ru"),
            hotkey=parser.get("hotkey", "key", fallback="ctrl_r"),
            auto_type=parser.getboolean("behavior", "auto_type", fallback=True),
            notifications=parser.getboolean("behavior", "notifications", fallback=True),
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
            "notifications": str(self.notifications).lower(),
        }

        with open(path, "w") as f:
            parser.write(f)
