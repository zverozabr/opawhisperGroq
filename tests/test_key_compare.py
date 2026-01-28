"""Tests for platform-specific key comparison."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from pynput import keyboard


class TestDefaultKeyComparer:
    """Tests for DefaultKeyComparer (Linux/Windows)."""

    def test_direct_match(self):
        """Direct key match returns True."""
        from soupawhisper.backend.key_compare_default import DefaultKeyComparer

        comparer = DefaultKeyComparer()
        assert comparer.keys_equal(keyboard.Key.ctrl_r, keyboard.Key.ctrl_r) is True

    def test_different_keys(self):
        """Different keys return False."""
        from soupawhisper.backend.key_compare_default import DefaultKeyComparer

        comparer = DefaultKeyComparer()
        assert comparer.keys_equal(keyboard.Key.ctrl_r, keyboard.Key.ctrl) is False

    def test_none_key(self):
        """None key returns False."""
        from soupawhisper.backend.key_compare_default import DefaultKeyComparer

        comparer = DefaultKeyComparer()
        assert comparer.keys_equal(None, keyboard.Key.ctrl_r) is False


class TestDarwinKeyComparer:
    """Tests for DarwinKeyComparer (macOS)."""

    def test_direct_match(self):
        """Direct key match returns True."""
        from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer

        comparer = DarwinKeyComparer()
        assert comparer.keys_equal(keyboard.Key.cmd_r, keyboard.Key.cmd_r) is True

    def test_vk_match(self):
        """Keys with same vk code match."""
        from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer

        comparer = DarwinKeyComparer()

        # Simulate a _darwin.KeyCode with same vk as Key.cmd_r
        mock_pressed = MagicMock()
        mock_pressed.vk = keyboard.Key.cmd_r.value.vk

        assert comparer.keys_equal(mock_pressed, keyboard.Key.cmd_r) is True

    def test_vk_mismatch(self):
        """Keys with different vk codes don't match."""
        from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer

        comparer = DarwinKeyComparer()

        # Simulate a _darwin.KeyCode with different vk
        mock_pressed = MagicMock()
        mock_pressed.vk = 999

        assert comparer.keys_equal(mock_pressed, keyboard.Key.cmd_r) is False

    def test_no_vk_attribute(self):
        """Key without vk attribute returns False."""
        from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer

        comparer = DarwinKeyComparer()

        # Object without vk attribute
        mock_pressed = MagicMock(spec=[])  # Empty spec = no attributes

        assert comparer.keys_equal(mock_pressed, keyboard.Key.cmd_r) is False


class TestKeyComparerFactory:
    """Tests for get_key_comparer factory."""

    def test_darwin_returns_darwin_comparer(self):
        """Factory returns DarwinKeyComparer on macOS."""
        with patch.object(sys, "platform", "darwin"):
            # Need to reimport to get fresh factory
            from importlib import reload

            from soupawhisper.backend import key_compare

            reload(key_compare)

            from soupawhisper.backend.key_compare import get_key_comparer
            from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer

            comparer = get_key_comparer()
            assert isinstance(comparer, DarwinKeyComparer)

    def test_linux_returns_default_comparer(self):
        """Factory returns DefaultKeyComparer on Linux."""
        with patch.object(sys, "platform", "linux"):
            from importlib import reload

            from soupawhisper.backend import key_compare

            reload(key_compare)

            from soupawhisper.backend.key_compare import get_key_comparer
            from soupawhisper.backend.key_compare_default import DefaultKeyComparer

            comparer = get_key_comparer()
            assert isinstance(comparer, DefaultKeyComparer)

    def test_windows_returns_default_comparer(self):
        """Factory returns DefaultKeyComparer on Windows."""
        with patch.object(sys, "platform", "win32"):
            from importlib import reload

            from soupawhisper.backend import key_compare

            reload(key_compare)

            from soupawhisper.backend.key_compare import get_key_comparer
            from soupawhisper.backend.key_compare_default import DefaultKeyComparer

            comparer = get_key_comparer()
            assert isinstance(comparer, DefaultKeyComparer)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
class TestDarwinIntegration:
    """Integration tests for macOS key comparison."""

    def test_cmd_r_vk_matches(self):
        """Key.cmd_r has expected vk value."""
        # cmd_r should have vk=54 on macOS
        assert hasattr(keyboard.Key.cmd_r, "value")
        assert hasattr(keyboard.Key.cmd_r.value, "vk")
        assert keyboard.Key.cmd_r.value.vk == 54

    def test_super_r_mapping_works_with_darwin_comparer(self):
        """super_r hotkey works with Darwin comparer."""
        from soupawhisper.backend.key_compare_darwin import DarwinKeyComparer
        from soupawhisper.backend.keys import get_pynput_keys

        comparer = DarwinKeyComparer()
        hotkeys = get_pynput_keys("super_r")

        # Simulate what pynput returns on macOS when cmd_r is pressed
        mock_pressed = MagicMock()
        mock_pressed.vk = 54  # cmd_r vk code

        # Should match
        assert any(comparer.keys_equal(mock_pressed, hk) for hk in hotkeys)
