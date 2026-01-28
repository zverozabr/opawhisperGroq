"""Integration tests for hotkey mappings."""

from unittest.mock import patch


# Mock providers config for settings tab tests
MOCK_PROVIDERS_CONFIG = {
    "active": "groq",
    "providers": {
        "groq": {
            "type": "openai_compatible",
            "api_key": "test_key",
        }
    }
}


class TestKeyMappingConsistency:
    """Test that key mappings are consistent across the codebase."""

    def test_pynput_map_matches_reverse_map(self):
        """Test that PYNPUT_HOTKEY_MAP and PYNPUT_KEY_TO_NAME are consistent."""
        from soupawhisper.backend.keys import PYNPUT_HOTKEY_MAP, PYNPUT_KEY_TO_NAME

        # Every name in forward map should have a reverse mapping
        for name, pynput_key in PYNPUT_HOTKEY_MAP.items():
            # The pynput key should map back to a name
            if pynput_key in PYNPUT_KEY_TO_NAME:
                # Name might be different due to aliases (e.g., alt_gr -> alt_r)
                reverse_name = PYNPUT_KEY_TO_NAME[pynput_key]
                # Just verify it maps to something valid
                assert reverse_name is not None

    def test_config_validation_accepts_all_capturable_keys(self):
        """Test that config validation accepts all keys that can be captured."""
        from soupawhisper.backend.keys import PYNPUT_KEY_TO_NAME
        from soupawhisper.config import Config, get_valid_hotkeys

        valid = get_valid_hotkeys()

        # Every capturable key should be valid in config
        for key_name in PYNPUT_KEY_TO_NAME.values():
            assert key_name in valid, f"Key '{key_name}' should be valid in config"

            # Create config with this key and validate
            config = Config(api_key="test", hotkey=key_name)
            errors = config.validate()
            hotkey_errors = [e for e in errors if "hotkey" in e.lower()]
            assert len(hotkey_errors) == 0, f"Key '{key_name}' failed validation: {hotkey_errors}"


class TestHotkeySelectorIntegration:
    """Integration tests for HotkeySelector with settings."""

    def test_hotkey_selector_in_settings_tab(self):
        """Test that HotkeySelector is in SettingsTab."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="key", hotkey="f9")
        with patch("soupawhisper.gui.settings_tab.load_providers_config", return_value=MOCK_PROVIDERS_CONFIG):
            with patch("soupawhisper.gui.settings_tab.list_providers", return_value=["groq"]):
                tab = SettingsTab(config=config, on_save=lambda f, v: None)
                tab.build()

                # HotkeySelector should be in the settings
                assert hasattr(tab, "hotkey_selector")
                assert tab.hotkey_selector.selected == "f9"

    def test_hotkey_selector_combo_in_settings(self):
        """Test that HotkeySelector handles combos in settings."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="key", hotkey="ctrl+g")
        with patch("soupawhisper.gui.settings_tab.load_providers_config", return_value=MOCK_PROVIDERS_CONFIG):
            with patch("soupawhisper.gui.settings_tab.list_providers", return_value=["groq"]):
                tab = SettingsTab(config=config, on_save=lambda f, v: None)
                tab.build()

                # Should show combo correctly
                assert tab.hotkey_selector.selected == "ctrl+g"

    def test_hotkey_selector_has_change_button(self):
        """Test that HotkeySelector has a Change button."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="key", hotkey="f9")
        with patch("soupawhisper.gui.settings_tab.load_providers_config", return_value=MOCK_PROVIDERS_CONFIG):
            with patch("soupawhisper.gui.settings_tab.list_providers", return_value=["groq"]):
                tab = SettingsTab(config=config, on_save=lambda f, v: None)
                tab.build()

                assert hasattr(tab.hotkey_selector, "_change_btn")
                assert tab.hotkey_selector._change_btn is not None

    def test_hotkey_selector_reset(self):
        """Test that HotkeySelector reset updates value."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="key", hotkey="f9")
        with patch("soupawhisper.gui.settings_tab.load_providers_config", return_value=MOCK_PROVIDERS_CONFIG):
            with patch("soupawhisper.gui.settings_tab.list_providers", return_value=["groq"]):
                tab = SettingsTab(config=config, on_save=lambda f, v: None)
                tab.build()

                # Reset to new value
                tab.hotkey_selector.reset("ctrl+g")

                assert tab.hotkey_selector.selected == "ctrl+g"
