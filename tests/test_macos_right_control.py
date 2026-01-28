"""Tests for macOS Right Control workaround.

Flutter bug #148936: Right Control key doesn't work on macOS with the new keyboard API.
https://github.com/flutter/flutter/issues/148936

These tests verify our workaround for detecting Right Control in the GUI.
"""

import sys

import pytest


class TestMacOSRightControlWorkaround:
    """Test workaround for Flutter bug #148936 on macOS."""

    def test_empty_key_with_ctrl_flag_treated_as_ctrl_r(self):
        """When e.key is empty but ctrl=True, treat as ctrl_r on macOS.

        On macOS, Flutter bug causes Right Control to not return a key name,
        but the ctrl flag is still set. We detect this and treat it as ctrl_r.
        """
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Simulate macOS Flutter bug: ctrl pressed but no key name
        kb.handle_physical_key_with_modifiers(key="", ctrl=True)

        assert kb._modifier == "ctrl_r", "Empty key + ctrl=True should select ctrl_r"
        assert kb.selected == "ctrl_r"

    def test_empty_key_with_alt_flag_treated_as_alt_r(self):
        """When e.key is empty but alt=True, treat as alt_r.

        Similar workaround for Alt key if Flutter has the same bug.
        """
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        kb.handle_physical_key_with_modifiers(key="", alt=True)

        assert kb._modifier == "alt_r", "Empty key + alt=True should select alt_r"

    def test_empty_key_with_meta_flag_treated_as_super_r(self):
        """When e.key is empty but meta=True, treat as super_r."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        kb.handle_physical_key_with_modifiers(key="", meta=True)

        assert kb._modifier == "super_r", "Empty key + meta=True should select super_r"

    def test_empty_key_with_shift_flag_detects_shift_r(self):
        """When e.key is empty but shift=True, detect as shift_r.

        Note: shift_r is not in the virtual keyboard layout, so it won't
        be selected, but _detect_modifier_from_flags should return it.
        """
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # The detection should work
        result = kb._detect_modifier_from_flags(key="", ctrl=False, alt=False, shift=True, meta=False)
        assert result == "shift_r", "Empty key + shift=True should detect as shift_r"

        # But selecting it won't work since shift_r isn't in keyboard layout
        # This is expected - shift keys are not typically hotkey-only keys

    def test_normal_key_not_affected_by_workaround(self):
        """Normal key presses should work as before."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Normal F9 press
        kb.handle_physical_key_with_modifiers(key="F9", ctrl=False)

        assert kb._key == "f9"
        assert kb.selected == "f9"

    def test_ctrl_left_still_works(self):
        """Control Left should still be detected normally."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Control Left returns proper key name
        kb.handle_physical_key_with_modifiers(key="Control Left", ctrl=True)

        assert kb._modifier == "ctrl_l"
        assert kb.selected == "ctrl_l"


class TestPynputRightControlSupport:
    """Verify pynput supports Right Control key."""

    def test_pynput_has_ctrl_r_key(self):
        """pynput should have ctrl_r defined."""
        from pynput.keyboard import Key

        assert hasattr(Key, "ctrl_r"), "pynput should have ctrl_r key"
        assert Key.ctrl_r is not None

    def test_pynput_has_all_right_modifiers(self):
        """pynput should have all right-side modifier keys."""
        from pynput.keyboard import Key

        right_modifiers = ["ctrl_r", "alt_r", "shift_r"]
        for mod in right_modifiers:
            assert hasattr(Key, mod), f"pynput should have {mod} key"

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific")
    def test_pynput_cmd_r_on_macos(self):
        """On macOS, pynput should have cmd_r (Right Command)."""
        from pynput.keyboard import Key

        # On macOS, cmd is mapped to super
        assert hasattr(Key, "cmd_r") or hasattr(Key, "cmd"), "pynput should have cmd key on macOS"


class TestHotkeySelectorModifierDetection:
    """Test that HotkeySelector properly detects modifiers."""

    def test_detect_modifier_from_empty_key_ctrl(self):
        """Detect ctrl_r when key is empty but ctrl flag is set."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # This simulates what Flet sends on macOS for Right Control
        result = kb._detect_modifier_from_flags(key="", ctrl=True, alt=False, shift=False, meta=False)

        assert result == "ctrl_r"

    def test_detect_modifier_priority(self):
        """When multiple flags set, ctrl takes priority."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Multiple flags - ctrl should take priority
        result = kb._detect_modifier_from_flags(key="", ctrl=True, alt=True, shift=False, meta=False)

        assert result == "ctrl_r"

    def test_no_detection_when_key_present(self):
        """Don't use workaround when key name is present."""
        from soupawhisper.gui.keyboard import VirtualKeyboard

        kb = VirtualKeyboard()

        # Key name present - no workaround needed
        result = kb._detect_modifier_from_flags(key="Control Left", ctrl=True, alt=False, shift=False, meta=False)

        assert result is None, "Should not use workaround when key name is present"
