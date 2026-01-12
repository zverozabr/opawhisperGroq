"""Tests for hotkey functionality."""

from pynput import keyboard

from soupawhisper.config import Config


class TestConfigHotkeyValidation:
    """Tests for hotkey validation in config."""

    def test_valid_hotkeys_from_mapping(self):
        """Test that get_valid_hotkeys returns all mapped keys."""
        from soupawhisper.config import get_valid_hotkeys
        from soupawhisper.backend.keys import PYNPUT_KEY_TO_NAME

        valid = get_valid_hotkeys()

        # Should contain all reverse-mapped keys
        for key_name in PYNPUT_KEY_TO_NAME.values():
            assert key_name in valid

    def test_config_validates_new_hotkeys(self):
        """Test that config validates new hotkey values."""
        from soupawhisper.config import get_valid_hotkeys

        valid = get_valid_hotkeys()

        # Should include F keys
        assert "f9" in valid
        assert "f10" in valid
        assert "f11" in valid
        assert "f12" in valid

        # Should include modifiers
        assert "ctrl_r" in valid
        assert "ctrl_l" in valid
        assert "alt_r" in valid
        assert "alt_l" in valid

    def test_config_validation_accepts_valid_hotkey(self):
        """Test that config validation accepts valid hotkeys."""
        config = Config(api_key="key", hotkey="f9")
        errors = config.validate()

        # Should not have hotkey error
        hotkey_errors = [e for e in errors if "hotkey" in e.lower()]
        assert len(hotkey_errors) == 0

    def test_config_validation_rejects_invalid_hotkey(self):
        """Test that config validation rejects invalid hotkeys."""
        config = Config(api_key="key", hotkey="invalid_key_xyz")
        errors = config.validate()

        # Should have hotkey error
        hotkey_errors = [e for e in errors if "hotkey" in e.lower()]
        assert len(hotkey_errors) == 1


class TestSettingsTabHotkey:
    """Tests for hotkey in SettingsTab."""

    def test_settings_tab_has_hotkey_selector(self):
        """Test that SettingsTab has hotkey_selector field."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="key", hotkey="ctrl_r")
        tab = SettingsTab(
            config=config,
            on_save=lambda field, value: None,
        )
        tab.build()

        assert hasattr(tab, "hotkey_selector")

    def test_settings_tab_hotkey_value(self):
        """Test that hotkey_selector has correct initial value."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="key", hotkey="f12")
        tab = SettingsTab(
            config=config,
            on_save=lambda field, value: None,
        )
        tab.build()

        assert tab.hotkey_selector.selected == "f12"

    def test_settings_tab_save_hotkey(self):
        """Test that saving hotkey calls callback."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="key", hotkey="ctrl_r")
        saved = []

        tab = SettingsTab(
            config=config,
            on_save=lambda field, value: saved.append((field, value)),
        )
        tab.build()

        # Simulate saving hotkey
        tab._save_field("hotkey", "f9")

        assert ("hotkey", "f9") in saved

    def test_update_config_resets_hotkey_selector(self):
        """Test that update_config resets hotkey_selector."""
        from soupawhisper.gui.settings_tab import SettingsTab

        config = Config(api_key="key", hotkey="ctrl_r")
        tab = SettingsTab(
            config=config,
            on_save=lambda field, value: None,
        )
        tab.build()

        # Update with new config
        new_config = Config(api_key="key2", hotkey="f10")
        tab.update_config(new_config)

        assert tab.hotkey_selector.selected == "f10"


class TestPynputKeyMapping:
    """Tests for pynput key mapping."""

    def test_get_pynput_key_simple(self):
        """Test simple key mapping."""
        from soupawhisper.backend.keys import get_pynput_key

        assert get_pynput_key("f9") == keyboard.Key.f9
        assert get_pynput_key("f12") == keyboard.Key.f12
        assert get_pynput_key("ctrl_r") == keyboard.Key.ctrl_r

    def test_get_pynput_key_combo(self):
        """Test combo key mapping returns key part."""
        from soupawhisper.backend.keys import get_pynput_key

        # For "ctrl+g" should return the key "g"
        key = get_pynput_key("ctrl+g")
        assert key == keyboard.KeyCode.from_char("g")

    def test_get_pynput_key_single_char(self):
        """Test single character key mapping."""
        from soupawhisper.backend.keys import get_pynput_key

        key = get_pynput_key("a")
        assert key == keyboard.KeyCode.from_char("a")

    def test_get_pynput_special_key(self):
        """Test special key mapping."""
        from soupawhisper.backend.keys import get_pynput_special_key

        assert get_pynput_special_key("enter") == keyboard.Key.enter
        assert get_pynput_special_key("tab") == keyboard.Key.tab
        assert get_pynput_special_key("space") == keyboard.Key.space

    def test_get_pynput_special_key_unknown(self):
        """Test unknown special key returns None."""
        from soupawhisper.backend.keys import get_pynput_special_key

        assert get_pynput_special_key("unknown") is None

    def test_get_pynput_keys_alt_r_has_aliases(self):
        """Test alt_r returns both alt_r and alt_gr variants."""
        from soupawhisper.backend.keys import get_pynput_keys

        keys = get_pynput_keys("alt_r")
        assert keyboard.Key.alt_r in keys
        assert keyboard.Key.alt_gr in keys
        assert len(keys) == 2

    def test_get_pynput_keys_regular_key_single(self):
        """Test regular keys return single key list."""
        from soupawhisper.backend.keys import get_pynput_keys

        keys = get_pynput_keys("ctrl_r")
        assert keys == [keyboard.Key.ctrl_r]
        
        keys = get_pynput_keys("f9")
        assert keys == [keyboard.Key.f9]
