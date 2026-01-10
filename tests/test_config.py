"""Tests for configuration."""

import tempfile
from pathlib import Path

import pytest

from soupawhisper.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self):
        """Test default config values."""
        config = Config(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == "whisper-large-v3"
        assert config.language == "auto"
        assert config.hotkey == "ctrl_r"
        assert config.auto_type is True
        assert config.auto_enter is False
        assert config.typing_delay == 12
        assert config.notifications is True
        assert config.backend == "auto"

    def test_save_and_load(self):
        """Test config save and load roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            config = Config(
                api_key="my-secret-key",
                model="whisper-large-v3-turbo",
                language="ru",
                hotkey="f12",
                auto_type=False,
                auto_enter=True,
                typing_delay=0,
                notifications=False,
                backend="wayland",
            )
            config.save(config_path)

            loaded = Config.load(config_path)

            assert loaded.api_key == "my-secret-key"
            assert loaded.model == "whisper-large-v3-turbo"
            assert loaded.language == "ru"
            assert loaded.hotkey == "f12"
            assert loaded.auto_type is False
            assert loaded.auto_enter is True
            assert loaded.typing_delay == 0
            assert loaded.notifications is False
            assert loaded.backend == "wayland"

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        config = Config.load(Path("/nonexistent/config.ini"))

        assert config.api_key == ""
        assert config.language == "auto"
        assert config.typing_delay == 12
        assert config.backend == "auto"
