"""Tests for settings persistence in GUI."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


from soupawhisper.config import Config


class TestSettingsTabFieldSave:
    """Tests for SettingsTab field-level saving."""

    def test_save_field_calls_callback(self):
        """Test that saving a field calls the on_save callback."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="old_key")
        saved_fields = []

        def on_save(field_name, value):
            saved_fields.append((field_name, value))

        tab = SettingsTab(config=config, on_save=on_save)
        tab.build()

        # Simulate saving api_key field
        tab._save_field("api_key", "new_key")

        assert len(saved_fields) == 1
        assert saved_fields[0] == ("api_key", "new_key")

    def test_save_field_updates_local_config(self):
        """Test that saving a field updates the local config."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="old_key")
        tab = SettingsTab(config=config, on_save=MagicMock())
        tab.build()

        tab._save_field("api_key", "new_key")

        assert tab.config.api_key == "new_key"

    def test_update_config_resets_all_fields(self):
        """Test that update_config resets all editable fields."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="old_key", language="en")
        tab = SettingsTab(config=config, on_save=MagicMock())
        tab.build()

        # Update with new config
        new_config = Config(api_key="new_key", language="ru")
        tab.update_config(new_config)

        assert tab.config.api_key == "new_key"
        assert tab.api_key_editable._initial_value == "new_key"


class TestGUIAppFieldSave:
    """Tests for GUIApp field-level saving."""

    def test_save_field_updates_config(self):
        """Test that _save_field updates config attribute."""
        from soupawhisper.gui.app import GUIApp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            with patch("soupawhisper.gui.app.CONFIG_PATH", config_path):
                with patch("soupawhisper.gui.app.Config.load") as mock_load:
                    mock_load.return_value = Config(api_key="old_key")
                    app = GUIApp()

                    app._save_field("api_key", "new_key")

                    assert app.config.api_key == "new_key"

    def test_save_field_persists_to_file(self):
        """Test that _save_field saves to config file."""
        from soupawhisper.gui.app import GUIApp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            # Create initial config
            initial_config = Config(api_key="old_key")
            initial_config.save(config_path)

            with patch("soupawhisper.gui.app.CONFIG_PATH", config_path):
                with patch("soupawhisper.gui.app.Config.load", return_value=Config.load(config_path)):
                    app = GUIApp()
                    app._save_field("api_key", "new_key")

            # Reload and verify
            reloaded = Config.load(config_path)
            assert reloaded.api_key == "new_key"

    def test_save_history_days_updates_history_tab(self):
        """Test that saving history_days updates history tab."""
        from soupawhisper.gui.app import GUIApp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            with patch("soupawhisper.gui.app.CONFIG_PATH", config_path):
                with patch("soupawhisper.gui.app.Config.load") as mock_load:
                    mock_load.return_value = Config(api_key="key", history_days=3)
                    app = GUIApp()

                    # Mock history tab
                    app.history_tab = MagicMock()
                    app.history_tab.history_days = 3

                    app._save_field("history_days", 7)

                    assert app.history_tab.history_days == 7
                    app.history_tab.refresh.assert_called_once()


class TestConfigFilePersistence:
    """Tests for config file persistence."""

    def test_config_saved_to_file(self):
        """Test that config is actually saved to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            config = Config(api_key="test_key_12345")
            config.save(config_path)

            reloaded = Config.load(config_path)
            assert reloaded.api_key == "test_key_12345"

    def test_all_fields_preserved_on_save(self):
        """Test that all fields are preserved when saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            config = Config(
                api_key="original_key",
                model="whisper-large-v3",
                language="ru",
                hotkey="ctrl_r",
                auto_type=True,
                auto_enter=True,
                typing_delay=20,
                notifications=True,
                backend="wayland",
                audio_device="hw:0",
                history_enabled=True,
                history_days=7,
                debug=True,
            )
            config.save(config_path)

            reloaded = Config.load(config_path)
            assert reloaded.api_key == "original_key"
            assert reloaded.model == "whisper-large-v3"
            assert reloaded.language == "ru"
            assert reloaded.debug is True
            assert reloaded.history_days == 7

    def test_single_field_update_preserves_others(self):
        """Test that updating one field preserves others."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"

            # Create config with all fields
            config = Config(
                api_key="original_key",
                debug=True,
                history_days=7,
            )
            config.save(config_path)

            # Reload, modify one field, save
            config2 = Config.load(config_path)
            config2.api_key = "new_key"
            config2.save(config_path)

            # Verify other fields preserved
            final = Config.load(config_path)
            assert final.api_key == "new_key"
            assert final.debug is True
            assert final.history_days == 7
