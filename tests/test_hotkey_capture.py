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


class TestVirtualKeyboardPhysicalInput:
    """Tests for physical keyboard input in VirtualKeyboard (TDD)."""

    def test_handle_physical_key_f12(self):
        """Physical F12 press should update selection."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        selected = []
        kb = VirtualKeyboard(on_change=lambda v: selected.append(v))

        # Simulate physical F12 press
        kb.handle_physical_key("F12")

        assert kb.selected == "f12"
        assert "f12" in selected

    def test_handle_physical_key_modifier(self):
        """Physical modifier key should update selection."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Simulate physical Right Ctrl press
        kb.handle_physical_key("Control Right")

        assert kb._modifier == "ctrl_r"

    def test_handle_physical_key_super_r(self):
        """Physical Right Super/Meta should update selection."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Simulate physical Right Meta/Super press
        kb.handle_physical_key("Meta Right")

        assert kb._modifier == "super_r"
        assert kb.selected == "super_r"

    def test_handle_physical_key_combo(self):
        """Physical key combo should work."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # First press modifier
        kb.handle_physical_key("Control Left")
        assert kb._modifier == "ctrl_l"

        # Then press letter
        kb.handle_physical_key("G")
        assert kb._key == "g"
        assert kb.selected == "ctrl_l+g"

    def test_normalize_key_name_function_keys(self):
        """Test key name normalization for function keys."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Function keys should normalize to lowercase
        assert kb._normalize_key_name("F1") == "f1"
        assert kb._normalize_key_name("F12") == "f12"

    def test_normalize_key_name_modifiers(self):
        """Test key name normalization for modifiers."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        assert kb._normalize_key_name("Control Left") == "ctrl_l"
        assert kb._normalize_key_name("Control Right") == "ctrl_r"
        assert kb._normalize_key_name("Alt Left") == "alt_l"
        assert kb._normalize_key_name("Alt Right") == "alt_r"
        assert kb._normalize_key_name("Meta Left") == "super_l"
        assert kb._normalize_key_name("Meta Right") == "super_r"

    def test_normalize_key_name_letters(self):
        """Test key name normalization for letters."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        assert kb._normalize_key_name("A") == "a"
        assert kb._normalize_key_name("Z") == "z"

    def test_handle_physical_key_unknown(self):
        """Unknown key should not crash."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Should not raise
        kb.handle_physical_key("Unknown Key 123")
        assert kb.selected is None


class TestPlatformAwareKeyNames:
    """Tests for platform-specific modifier key names (TDD)."""

    def test_get_modifier_display_macos_symbol(self):
        """On macOS, get_modifier_display returns symbols by default."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_modifier_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "darwin"):
            assert get_modifier_display("super_l") == "⌘"
            assert get_modifier_display("super_r") == "⌘"
            assert get_modifier_display("alt_l") == "⌥"
            assert get_modifier_display("alt_r") == "⌥"
            assert get_modifier_display("ctrl_l") == "⌃"
            assert get_modifier_display("shift_l") == "⇧"

    def test_get_modifier_display_macos_name(self):
        """On macOS, get_modifier_display returns full names when requested."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_modifier_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "darwin"):
            assert get_modifier_display("super_l", use_symbol=False) == "Command"
            assert get_modifier_display("super_r", use_symbol=False) == "Command"
            assert get_modifier_display("alt_l", use_symbol=False) == "Option"
            assert get_modifier_display("alt_r", use_symbol=False) == "Option"
            assert get_modifier_display("ctrl_l", use_symbol=False) == "Control"

    def test_get_modifier_display_linux(self):
        """On Linux, get_modifier_display returns standard names."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_modifier_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "linux"):
            assert get_modifier_display("super_l") == "Left Super"
            assert get_modifier_display("super_r") == "Right Super"
            assert get_modifier_display("alt_l") == "Left Alt"
            assert get_modifier_display("ctrl_r") == "Right Ctrl"

    def test_get_modifier_display_windows(self):
        """On Windows, get_modifier_display returns standard names."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_modifier_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "win32"):
            assert get_modifier_display("super_l") == "Left Super"
            assert get_modifier_display("alt_r") == "Right Alt"

    def test_format_hotkey_display_macos(self):
        """format_hotkey_display uses platform names on macOS."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import format_hotkey_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "darwin"):
            # Single modifier
            assert "Command" in format_hotkey_display("super_r")
            # Combo
            display = format_hotkey_display("super_l+g")
            assert "Command" in display
            assert "G" in display

    def test_format_hotkey_display_linux(self):
        """format_hotkey_display uses standard names on Linux."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import format_hotkey_display

        with patch("soupawhisper.gui.hotkey.sys.platform", "linux"):
            assert "Super" in format_hotkey_display("super_r")
            display = format_hotkey_display("alt_l+f9")
            assert "Alt" in display

    def test_get_keyboard_layout_macos(self):
        """get_keyboard_layout returns macOS layout on darwin."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_keyboard_layout

        with patch("soupawhisper.gui.hotkey.sys.platform", "darwin"):
            layout = get_keyboard_layout()
            # Find modifier row and check for symbols
            modifier_row = layout[-2]  # Second to last row has modifiers
            labels = [item[1] for item in modifier_row]
            assert "⌘" in labels or any("⌘" in l for l in labels)

    def test_get_keyboard_layout_linux(self):
        """get_keyboard_layout returns default layout on Linux."""
        from unittest.mock import patch

        from soupawhisper.gui.hotkey import get_keyboard_layout

        with patch("soupawhisper.gui.hotkey.sys.platform", "linux"):
            layout = get_keyboard_layout()
            modifier_row = layout[-2]
            labels = [item[1] for item in modifier_row]
            # Should have text labels, not symbols
            assert any("Ctrl" in l or "Super" in l or "Alt" in l for l in labels)
