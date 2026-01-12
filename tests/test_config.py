"""Tests for configuration."""

import tempfile
from pathlib import Path


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
        assert config.audio_device == "default"
        assert config.history_enabled is True
        assert config.history_days == 3

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
                audio_device="hw:1,0",
                history_enabled=False,
                history_days=7,
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
            assert loaded.audio_device == "hw:1,0"
            assert loaded.history_enabled is False
            assert loaded.history_days == 7

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        config = Config.load(Path("/nonexistent/config.ini"))

        assert config.api_key == ""
        assert config.language == "auto"
        assert config.typing_delay == 12
        assert config.backend == "auto"

    def test_validate_valid_config(self):
        """Test validation passes for valid config."""
        config = Config(
            api_key="test-key",
            language="ru",
            hotkey="ctrl_r",
            backend="auto",
            typing_delay=12,
            history_days=3,
        )
        errors = config.validate()
        assert errors == []
        assert config.is_valid()

    def test_validate_invalid_language(self):
        """Test validation catches invalid language."""
        config = Config(api_key="test", language="invalid")
        errors = config.validate()
        assert any("language" in e.lower() for e in errors)
        assert not config.is_valid()

    def test_validate_invalid_hotkey(self):
        """Test validation catches invalid hotkey."""
        config = Config(api_key="test", hotkey="invalid_key")
        errors = config.validate()
        assert any("hotkey" in e.lower() for e in errors)

    def test_validate_invalid_backend(self):
        """Test validation catches invalid backend."""
        config = Config(api_key="test", backend="invalid_backend")
        errors = config.validate()
        assert any("backend" in e.lower() for e in errors)

    def test_validate_typing_delay_range(self):
        """Test typing_delay must be 0-1000."""
        config = Config(api_key="test", typing_delay=-1)
        assert not config.is_valid()

        config = Config(api_key="test", typing_delay=1001)
        assert not config.is_valid()

        config = Config(api_key="test", typing_delay=500)
        assert config.is_valid()

    def test_validate_history_days_range(self):
        """Test history_days must be 1-365."""
        config = Config(api_key="test", history_days=0)
        assert not config.is_valid()

        config = Config(api_key="test", history_days=366)
        assert not config.is_valid()

        config = Config(api_key="test", history_days=30)
        assert config.is_valid()
