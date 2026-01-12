"""Tests for virtual keyboard component."""

import pytest


class TestVirtualKeyboard:
    """Tests for VirtualKeyboard component."""

    def test_renders_all_keys(self):
        """Test that keyboard renders buttons for unique keys."""
        from soupawhisper.gui.components import VirtualKeyboard, KEYBOARD_LAYOUT

        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: None)

        # Count unique keys in layout (some keys appear multiple times like ctrl, alt, super)
        unique_keys = set(key for row in KEYBOARD_LAYOUT for key, _, _ in row)

        assert len(keyboard._buttons) == len(unique_keys)

    def test_initial_value_none(self):
        """Test no selection when initial_value is None."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: None)

        assert keyboard.selected is None

    def test_initial_single_key(self):
        """Test initial single key selection."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value="f9", on_change=lambda k: None)

        assert keyboard.selected == "f9"

    def test_initial_combo(self):
        """Test initial combo like ctrl+g."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value="ctrl+g", on_change=lambda k: None)

        assert keyboard.selected == "ctrl+g"
        assert keyboard._modifier == "ctrl"
        assert keyboard._key == "g"

    def test_select_function_key(self):
        """Test selecting function key without modifier."""
        from soupawhisper.gui.components import VirtualKeyboard

        changes = []
        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: changes.append(k))

        keyboard.select("f9")

        assert keyboard.selected == "f9"
        assert changes == ["f9"]

    def test_select_modifier_then_letter_makes_combo(self):
        """Test ctrl_l + g = ctrl_l+g combo."""
        from soupawhisper.gui.components import VirtualKeyboard

        changes = []
        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: changes.append(k))

        keyboard.select("ctrl_l")  # Select modifier
        keyboard.select("g")       # Select letter

        assert keyboard.selected == "ctrl_l+g"
        assert "ctrl_l+g" in changes

    def test_select_modifier_then_fkey_makes_combo(self):
        """Test alt_l + f9 = alt_l+f9 combo."""
        from soupawhisper.gui.components import VirtualKeyboard

        changes = []
        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: changes.append(k))

        keyboard.select("alt_l")
        keyboard.select("f9")

        assert keyboard.selected == "alt_l+f9"

    def test_letters_disabled_without_modifier(self):
        """Test that letter keys are disabled when no modifier selected."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: None)

        # Letter buttons should be disabled
        assert keyboard._buttons["a"].disabled is True
        assert keyboard._buttons["g"].disabled is True

    def test_letters_enabled_with_modifier(self):
        """Test that letter keys become enabled when modifier selected."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: None)

        keyboard.select("ctrl_l")  # Select modifier

        # Letter buttons should now be enabled
        assert keyboard._buttons["a"].disabled is False
        assert keyboard._buttons["g"].disabled is False

    def test_deselect_modifier_disables_letters(self):
        """Test that deselecting modifier disables letters again."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value=None, on_change=lambda k: None)

        keyboard.select("ctrl_l")  # Select
        keyboard.select("ctrl_l")  # Deselect

        assert keyboard._buttons["a"].disabled is True

    def test_click_same_key_deselects(self):
        """Test clicking same key deselects it."""
        from soupawhisper.gui.components import VirtualKeyboard

        changes = []
        keyboard = VirtualKeyboard(initial_value="f9", on_change=lambda k: changes.append(k))

        keyboard.select("f9")

        assert keyboard.selected is None
        assert None in changes

    def test_reset_updates_value(self):
        """Test reset() updates selection."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value="f9", on_change=lambda k: None)

        keyboard.reset("ctrl+g")

        assert keyboard.selected == "ctrl+g"

    def test_clear_clears_all(self):
        """Test clear() clears entire selection."""
        from soupawhisper.gui.components import VirtualKeyboard

        changes = []
        keyboard = VirtualKeyboard(initial_value="ctrl_l+g", on_change=lambda k: changes.append(k))

        keyboard.clear()

        assert keyboard.selected is None
        assert keyboard._modifier is None
        assert keyboard._key is None
        assert None in changes

    def test_toggle_modifier_in_combo(self):
        """Test clicking modifier again in combo removes just the modifier."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value="ctrl_l+g", on_change=lambda k: None)

        # Click ctrl_l to remove it from combo
        keyboard.select("ctrl_l")

        # Modifier should be gone but key stays (even though invalid alone)
        assert keyboard._modifier is None
        assert keyboard._key == "g"
        # Selection is None because letter alone is invalid
        assert keyboard.selected is None

    def test_toggle_key_in_combo(self):
        """Test clicking key again in combo removes just the key."""
        from soupawhisper.gui.components import VirtualKeyboard

        keyboard = VirtualKeyboard(initial_value="ctrl_l+g", on_change=lambda k: None)

        # Click g to remove it from combo
        keyboard.select("g")

        # Key should be gone but modifier stays
        assert keyboard._modifier == "ctrl_l"
        assert keyboard._key is None
        # Modifier-only is now valid for push-to-talk style
        assert keyboard.selected == "ctrl_l"
        assert keyboard.is_valid_hotkey is True


class TestKeyboardLayout:
    """Tests for keyboard layout."""

    def test_has_function_keys(self):
        """Test layout has F1-F12."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        for i in range(1, 13):
            assert f"f{i}" in all_keys

    def test_has_modifiers(self):
        """Test layout has modifier keys (left and right variants)."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        # Left modifiers
        assert "ctrl_l" in all_keys
        assert "alt_l" in all_keys
        assert "super_l" in all_keys
        # Right modifiers
        assert "ctrl_r" in all_keys
        assert "alt_r" in all_keys
        assert "super_r" in all_keys

    def test_has_letters(self):
        """Test layout has letter keys a-z."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        for letter in "qwertyuiopasdfghjklzxcvbnm":
            assert letter in all_keys

    def test_has_special_keys(self):
        """Test layout has special keys."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        assert "space" in all_keys
        assert "enter" in all_keys
        assert "tab" in all_keys
        assert "escape" in all_keys

    def test_has_navigation_keys(self):
        """Test layout has navigation keys."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        # Arrow keys
        assert "up" in all_keys
        assert "down" in all_keys
        assert "left" in all_keys
        assert "right" in all_keys
        # Page keys
        assert "home" in all_keys
        assert "end" in all_keys
        assert "page_up" in all_keys
        assert "page_down" in all_keys
        # Insert/Delete
        assert "insert" in all_keys
        assert "delete" in all_keys

    def test_has_lock_keys(self):
        """Test layout has lock keys."""
        from soupawhisper.gui.components import KEYBOARD_LAYOUT

        all_keys = [key for row in KEYBOARD_LAYOUT for key, _, _ in row]

        assert "num_lock" in all_keys
        assert "scroll_lock" in all_keys
        assert "caps_lock" in all_keys
        assert "print_screen" in all_keys


class TestHotkeyParsing:
    """Tests for hotkey string parsing."""

    def test_parse_single_key(self):
        """Test parsing single key like f9."""
        from soupawhisper.gui.components import parse_hotkey

        modifier, key = parse_hotkey("f9")

        assert modifier is None
        assert key == "f9"

    def test_parse_combo(self):
        """Test parsing combo like ctrl+g."""
        from soupawhisper.gui.components import parse_hotkey

        modifier, key = parse_hotkey("ctrl+g")

        assert modifier == "ctrl"
        assert key == "g"

    def test_parse_modifier_only(self):
        """Test parsing modifier alone like ctrl_r returns (modifier, None)."""
        from soupawhisper.gui.components import parse_hotkey

        modifier, key = parse_hotkey("ctrl_r")

        # Modifier-only keys are returned as (modifier, None) for proper dropdown sync
        assert modifier == "ctrl_r"
        assert key is None

    def test_format_combo(self):
        """Test formatting combo string."""
        from soupawhisper.gui.components import format_hotkey

        result = format_hotkey("ctrl", "g")

        assert result == "ctrl+g"

    def test_format_single(self):
        """Test formatting single key."""
        from soupawhisper.gui.components import format_hotkey

        result = format_hotkey(None, "f9")

        assert result == "f9"


class TestHotkeySelector:
    """Tests for HotkeySelector component."""

    def test_initial_value(self):
        """Test initial value is displayed."""
        from soupawhisper.gui.components import HotkeySelector

        selector = HotkeySelector(initial_value="f9", on_save=lambda v: None)

        assert selector.value == "f9"
        assert selector.selected == "f9"

    def test_reset_updates_value(self):
        """Test reset() updates the value."""
        from soupawhisper.gui.components import HotkeySelector

        selector = HotkeySelector(initial_value="f9", on_save=lambda v: None)

        selector.reset("ctrl+g")

        assert selector.value == "ctrl+g"

    def test_has_change_button(self):
        """Test selector has a Change button."""
        from soupawhisper.gui.components import HotkeySelector

        selector = HotkeySelector(initial_value="f9", on_save=lambda v: None)

        assert hasattr(selector, "_change_btn")
        assert selector._change_btn is not None


class TestFormatHotkeyDisplay:
    """Tests for hotkey display formatting."""

    def test_format_single_key(self):
        """Test formatting single key for display."""
        from soupawhisper.gui.components import format_hotkey_display

        assert format_hotkey_display("f9") == "F9"
        assert format_hotkey_display("escape") == "Escape"
        assert format_hotkey_display("ctrl_r") == "Right Ctrl"

    def test_format_combo(self):
        """Test formatting combo for display."""
        from soupawhisper.gui.components import format_hotkey_display

        assert format_hotkey_display("ctrl+g") == "Ctrl + G"
        assert format_hotkey_display("alt+f9") == "Alt + F9"

    def test_format_none(self):
        """Test formatting None."""
        from soupawhisper.gui.components import format_hotkey_display

        assert format_hotkey_display(None) == "Not set"
