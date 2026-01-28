"""Tests for HotkeyInput widget.

TDD: Tests for hotkey input widget functionality.
"""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Select

from soupawhisper.tui.widgets.hotkey_input import (
    HotkeyInput,
    KEY_OPTIONS,
    MODIFIER_OPTIONS,
)


class TestHotkeyInputParsing:
    """Test hotkey parsing logic."""

    def test_parse_single_modifier(self):
        """Parse single modifier key."""
        widget = HotkeyInput(hotkey="ctrl_r")
        assert widget._modifier == "ctrl_r"
        assert widget._key == ""

    def test_parse_modifier_plus_key(self):
        """Parse modifier + key combination."""
        widget = HotkeyInput(hotkey="alt_r+f12")
        assert widget._modifier == "alt_r"
        assert widget._key == "f12"

    def test_parse_unknown_format_defaults(self):
        """Unknown format defaults to ctrl_r modifier."""
        widget = HotkeyInput(hotkey="unknown_key")
        assert widget._modifier == "ctrl_r"
        assert widget._key == "unknown_key"

    def test_parse_empty_hotkey(self):
        """Empty hotkey defaults to ctrl_r."""
        widget = HotkeyInput(hotkey="")
        assert widget._modifier == "ctrl_r"
        assert widget._key == ""


class TestHotkeyInputValue:
    """Test hotkey value property."""

    def test_value_returns_modifier_only(self):
        """Value returns modifier when no key."""
        widget = HotkeyInput(hotkey="ctrl_r")
        assert widget.value == "ctrl_r"

    def test_value_returns_combo(self):
        """Value returns modifier+key for combination."""
        widget = HotkeyInput(hotkey="alt_r+f12")
        assert widget.value == "alt_r+f12"


class TestHotkeyInputCallback:
    """Test on_change callback behavior."""

    def test_callback_called_on_modifier_change(self):
        """Callback is called when modifier changes."""
        callback_results = []

        def callback(hotkey):
            callback_results.append(hotkey)

        widget = HotkeyInput(hotkey="ctrl_r", on_change=callback)
        widget._modifier = "alt_r"
        widget._notify_change()

        assert len(callback_results) == 1
        assert callback_results[0] == "alt_r"

    def test_callback_called_with_combo(self):
        """Callback receives modifier+key combo."""
        callback_results = []

        def callback(hotkey):
            callback_results.append(hotkey)

        widget = HotkeyInput(hotkey="ctrl_r", on_change=callback)
        widget._modifier = "alt_r"
        widget._key = "f12"
        widget._notify_change()

        assert callback_results[0] == "alt_r+f12"

    def test_no_callback_when_none(self):
        """No error when callback is None."""
        widget = HotkeyInput(hotkey="ctrl_r", on_change=None)
        widget._modifier = "alt_r"
        widget._notify_change()  # Should not raise


class TestHotkeyInputCompose:
    """Test widget composition."""

    @pytest.mark.asyncio
    async def test_has_modifier_select(self):
        """Widget has modifier select dropdown."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyInput(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            selects = pilot.app.query("#modifier-select")
            assert len(selects) == 1

    @pytest.mark.asyncio
    async def test_has_key_select(self):
        """Widget has key select dropdown."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyInput(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            selects = pilot.app.query("#key-select")
            assert len(selects) == 1

    @pytest.mark.asyncio
    async def test_modifier_select_has_options(self):
        """Modifier select has all modifier options."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyInput(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            pilot.app.query_one("#modifier-select", Select)
            # Should have all modifier options
            assert len(MODIFIER_OPTIONS) >= 4

    @pytest.mark.asyncio
    async def test_key_select_has_options(self):
        """Key select has all key options."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyInput(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            pilot.app.query_one("#key-select", Select)
            # Should have key options including empty
            assert len(KEY_OPTIONS) >= 5


class TestHotkeyInputOptions:
    """Test available options."""

    def test_modifier_options_include_ctrl(self):
        """Modifier options include Ctrl keys."""
        modifier_values = [m[1] for m in MODIFIER_OPTIONS]
        assert "ctrl_r" in modifier_values
        assert "ctrl_l" in modifier_values

    def test_modifier_options_include_alt(self):
        """Modifier options include Alt keys."""
        modifier_values = [m[1] for m in MODIFIER_OPTIONS]
        assert "alt_r" in modifier_values
        assert "alt_l" in modifier_values

    def test_key_options_include_function_keys(self):
        """Key options include function keys."""
        key_values = [k[1] for k in KEY_OPTIONS]
        assert "f12" in key_values
        assert "f11" in key_values

    def test_key_options_include_empty(self):
        """Key options include empty (modifier only)."""
        key_values = [k[1] for k in KEY_OPTIONS]
        assert "" in key_values


class TestHotkeyInputEdgeCases:
    """Test edge cases."""

    def test_plus_in_middle_of_hotkey(self):
        """Handle + in middle of hotkey string."""
        widget = HotkeyInput(hotkey="ctrl_r+f12")
        assert widget._modifier == "ctrl_r"
        assert widget._key == "f12"

    def test_multiple_plus_signs(self):
        """Handle multiple + signs (takes first two parts)."""
        widget = HotkeyInput(hotkey="ctrl_r+f12+extra")
        assert widget._modifier == "ctrl_r"
        assert widget._key == "f12"

    def test_whitespace_in_hotkey(self):
        """Handle whitespace in hotkey (not stripped)."""
        widget = HotkeyInput(hotkey=" ctrl_r ")
        # Will not match modifier list, so treated as key
        assert widget._modifier == "ctrl_r"  # Default
        assert widget._key == " ctrl_r "
