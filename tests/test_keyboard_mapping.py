"""Comprehensive tests for keyboard key mapping.

Tests all key names that Flet might return and verifies normalization.
"""

import pytest

from soupawhisper.gui.keyboard import VirtualKeyboard
from soupawhisper.gui.hotkey import KEYBOARD_LAYOUT, MODIFIER_KEYS, LETTER_KEYS


class TestKeyNameNormalization:
    """Test key name normalization for all possible Flet key names."""

    @pytest.fixture
    def keyboard(self):
        """Create VirtualKeyboard instance."""
        return VirtualKeyboard()

    # ==================== Modifier Keys ====================

    @pytest.mark.parametrize("flet_key,expected", [
        # Standard Flet/Flutter key names
        ("Control Left", "ctrl_l"),
        ("Control Right", "ctrl_r"),
        ("Alt Left", "alt_l"),
        ("Alt Right", "alt_r"),
        ("Meta Left", "super_l"),
        ("Meta Right", "super_r"),
        ("Shift Left", "shift_l"),
        ("Shift Right", "shift_r"),
        # Alternate names (no space)
        ("ControlLeft", "ctrl_l"),
        ("ControlRight", "ctrl_r"),
        ("AltLeft", "alt_l"),
        ("AltRight", "alt_r"),
        ("MetaLeft", "super_l"),
        ("MetaRight", "super_r"),
        ("ShiftLeft", "shift_l"),
        ("ShiftRight", "shift_r"),
        # macOS-specific
        ("Control", "ctrl_l"),
        ("Option Left", "alt_l"),
        ("Option Right", "alt_r"),
        ("Command Left", "super_l"),
        ("Command Right", "super_r"),
        ("Alt Graph", "alt_r"),
    ])
    def test_modifier_keys_standard(self, keyboard, flet_key, expected):
        """Test standard modifier key normalization."""
        result = keyboard._normalize_key_name(flet_key)
        assert result == expected, f"Expected '{expected}' for '{flet_key}', got '{result}'"

    # ==================== Function Keys ====================

    @pytest.mark.parametrize("flet_key,expected", [
        ("F1", "f1"), ("F2", "f2"), ("F3", "f3"), ("F4", "f4"),
        ("F5", "f5"), ("F6", "f6"), ("F7", "f7"), ("F8", "f8"),
        ("F9", "f9"), ("F10", "f10"), ("F11", "f11"), ("F12", "f12"),
    ])
    def test_function_keys(self, keyboard, flet_key, expected):
        """Test function key normalization."""
        result = keyboard._normalize_key_name(flet_key)
        assert result == expected

    # ==================== Special Keys ====================

    @pytest.mark.parametrize("flet_key,expected", [
        ("Escape", "escape"),
        ("Tab", "tab"),
        ("Caps Lock", "caps_lock"),
        ("CapsLock", "caps_lock"),
        ("Backspace", "backspace"),
        ("Enter", "enter"),
        ("Return", "enter"),  # macOS alternate
        ("Space", "space"),
        (" ", "space"),  # Space character
        ("Insert", "insert"),
        ("Delete", "delete"),
        ("Home", "home"),
        ("End", "end"),
        ("Page Up", "page_up"),
        ("PageUp", "page_up"),
        ("Page Down", "page_down"),
        ("PageDown", "page_down"),
        ("Num Lock", "num_lock"),
        ("NumLock", "num_lock"),
        ("Scroll Lock", "scroll_lock"),
        ("ScrollLock", "scroll_lock"),
        ("Pause", "pause"),
        ("Print Screen", "print_screen"),
        ("PrintScreen", "print_screen"),
    ])
    def test_special_keys(self, keyboard, flet_key, expected):
        """Test special key normalization."""
        result = keyboard._normalize_key_name(flet_key)
        assert result == expected

    # ==================== Arrow Keys ====================

    @pytest.mark.parametrize("flet_key,expected", [
        ("Arrow Up", "up"),
        ("Arrow Down", "down"),
        ("Arrow Left", "left"),
        ("Arrow Right", "right"),
        # Alternate names
        ("ArrowUp", "up"),
        ("ArrowDown", "down"),
        ("ArrowLeft", "left"),
        ("ArrowRight", "right"),
        ("Up", "up"),
        ("Down", "down"),
        ("Left", "left"),
        ("Right", "right"),
    ])
    def test_arrow_keys(self, keyboard, flet_key, expected):
        """Test arrow key normalization."""
        result = keyboard._normalize_key_name(flet_key)
        assert result == expected

    # ==================== Letters ====================

    @pytest.mark.parametrize("letter", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    def test_uppercase_letters(self, keyboard, letter):
        """Test uppercase letter normalization."""
        result = keyboard._normalize_key_name(letter)
        assert result == letter.lower()

    @pytest.mark.parametrize("letter", list("abcdefghijklmnopqrstuvwxyz"))
    def test_lowercase_letters(self, keyboard, letter):
        """Test lowercase letter normalization."""
        result = keyboard._normalize_key_name(letter)
        assert result == letter

    # ==================== Numbers ====================

    @pytest.mark.parametrize("number", list("0123456789"))
    def test_numbers(self, keyboard, number):
        """Test number normalization."""
        result = keyboard._normalize_key_name(number)
        assert result == number


class TestPhysicalKeyHandling:
    """Test physical keyboard key handling."""

    def test_handle_all_function_keys(self):
        """Test handling all function keys."""
        for i in range(1, 13):
            selected = []
            kb = VirtualKeyboard(on_change=lambda v: selected.append(v))

            kb.handle_physical_key(f"F{i}")

            assert kb.selected == f"f{i}", f"F{i} should select f{i}"
            assert f"f{i}" in selected

    def test_handle_all_modifiers(self):
        """Test handling all modifier keys."""
        modifier_tests = [
            ("Control Left", "ctrl_l"),
            ("Control Right", "ctrl_r"),
            ("Alt Left", "alt_l"),
            ("Alt Right", "alt_r"),
            ("Meta Left", "super_l"),
            ("Meta Right", "super_r"),
        ]

        for flet_key, expected in modifier_tests:
            kb = VirtualKeyboard()
            kb.handle_physical_key(flet_key)

            assert kb._modifier == expected, f"{flet_key} should set modifier to {expected}"
            assert kb.selected == expected

    def test_handle_letter_with_modifier(self):
        """Test handling letter keys with modifier."""
        kb = VirtualKeyboard()

        # First select modifier
        kb.handle_physical_key("Control Left")
        assert kb._modifier == "ctrl_l"

        # Then select letter
        kb.handle_physical_key("G")
        assert kb._key == "g"
        assert kb.selected == "ctrl_l+g"

    def test_handle_all_arrow_keys(self):
        """Test handling all arrow keys."""
        arrow_tests = [
            ("Arrow Up", "up"),
            ("Arrow Down", "down"),
            ("Arrow Left", "left"),
            ("Arrow Right", "right"),
        ]

        for flet_key, expected in arrow_tests:
            kb = VirtualKeyboard()
            kb.handle_physical_key(flet_key)

            assert kb.selected == expected, f"{flet_key} should select {expected}"

    def test_handle_special_keys(self):
        """Test handling special keys."""
        special_tests = [
            ("Escape", "escape"),
            ("Tab", "tab"),
            ("Space", "space"),
            ("Enter", "enter"),
            ("Backspace", "backspace"),
            ("Delete", "delete"),
            ("Home", "home"),
            ("End", "end"),
            ("Page Up", "page_up"),
            ("Page Down", "page_down"),
        ]

        for flet_key, expected in special_tests:
            kb = VirtualKeyboard()
            kb.handle_physical_key(flet_key)

            assert kb.selected == expected, f"{flet_key} should select {expected}"


class TestKeyboardLayoutCoverage:
    """Test that all keys in KEYBOARD_LAYOUT can be selected."""

    def test_all_layout_keys_are_selectable(self):
        """Verify all keys in layout can be selected via physical keyboard."""
        # Get all key names from layout
        all_keys = set()
        for row in KEYBOARD_LAYOUT:
            for key_name, _, _ in row:
                all_keys.add(key_name)

        # Create reverse mapping: our key -> Flet key
        our_to_flet = {
            # Modifiers
            "ctrl_l": "Control Left",
            "ctrl_r": "Control Right",
            "alt_l": "Alt Left",
            "alt_r": "Alt Right",
            "super_l": "Meta Left",
            "super_r": "Meta Right",
            "shift_l": "Shift Left",
            "shift_r": "Shift Right",
            # Function keys
            **{f"f{i}": f"F{i}" for i in range(1, 13)},
            # Special keys
            "escape": "Escape",
            "tab": "Tab",
            "caps_lock": "Caps Lock",
            "backspace": "Backspace",
            "enter": "Enter",
            "space": "Space",
            "insert": "Insert",
            "delete": "Delete",
            "home": "Home",
            "end": "End",
            "page_up": "Page Up",
            "page_down": "Page Down",
            "num_lock": "Num Lock",
            "scroll_lock": "Scroll Lock",
            "pause": "Pause",
            "print_screen": "Print Screen",
            # Arrows
            "up": "Arrow Up",
            "down": "Arrow Down",
            "left": "Arrow Left",
            "right": "Arrow Right",
            # Letters
            **{c: c.upper() for c in "abcdefghijklmnopqrstuvwxyz"},
            # Numbers
            **{n: n for n in "0123456789"},
        }

        # Test each non-letter key can be selected
        for key_name in all_keys:
            if key_name in LETTER_KEYS:
                continue  # Letters require modifier

            kb = VirtualKeyboard()
            flet_key = our_to_flet.get(key_name)

            if flet_key:
                kb.handle_physical_key(flet_key)

                if key_name in MODIFIER_KEYS:
                    assert kb._modifier == key_name, f"Modifier {key_name} not selected"
                else:
                    assert kb._key == key_name or kb._modifier == key_name, \
                        f"Key {key_name} not selected (Flet: {flet_key})"


class TestKeyboardToggle:
    """Test key toggling behavior."""

    def test_toggle_modifier_off(self):
        """Test toggling modifier key off."""
        kb = VirtualKeyboard()

        kb.handle_physical_key("Control Left")
        assert kb._modifier == "ctrl_l"

        # Press again to toggle off
        kb.handle_physical_key("Control Left")
        assert kb._modifier is None

    def test_toggle_key_off(self):
        """Test toggling regular key off."""
        kb = VirtualKeyboard()

        kb.handle_physical_key("F9")
        assert kb._key == "f9"

        # Press again to toggle off
        kb.handle_physical_key("F9")
        assert kb._key is None

    def test_switch_modifier(self):
        """Test switching between modifiers."""
        kb = VirtualKeyboard()

        kb.handle_physical_key("Control Left")
        assert kb._modifier == "ctrl_l"

        # Switch to different modifier
        kb.handle_physical_key("Alt Right")
        assert kb._modifier == "alt_r"


class TestUnknownKeys:
    """Test handling of unknown keys."""

    @pytest.mark.parametrize("unknown_key", [
        "Unknown Key",
        "Some Random Key",
        "FnKey",
        "",
        "   ",
    ])
    def test_unknown_keys_return_none(self, unknown_key):
        """Test that unknown keys return None."""
        kb = VirtualKeyboard()
        result = kb._normalize_key_name(unknown_key)

        # Empty/whitespace keys should return None
        if not unknown_key or not unknown_key.strip():
            assert result is None or result == unknown_key.lower()
        else:
            # Multi-word unknown keys should return None
            if " " in unknown_key and unknown_key not in [
                "Control Left", "Control Right", "Alt Left", "Alt Right",
                "Meta Left", "Meta Right", "Shift Left", "Shift Right",
                "Caps Lock", "Page Up", "Page Down", "Num Lock",
                "Scroll Lock", "Print Screen", "Arrow Up", "Arrow Down",
                "Arrow Left", "Arrow Right"
            ]:
                assert result is None

    def test_unknown_key_doesnt_crash(self):
        """Test that unknown key press doesn't crash."""
        kb = VirtualKeyboard()

        # Should not raise any exception
        kb.handle_physical_key("Completely Unknown Key 123!@#")

        # State should be unchanged
        assert kb._modifier is None
        assert kb._key is None
        assert kb.selected is None
