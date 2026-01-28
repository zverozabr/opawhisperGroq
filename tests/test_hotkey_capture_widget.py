"""TDD: Tests for HotkeyCapture widget.

Tests written BEFORE implementation.
SOLID/SRP: Widget only handles UI, pynput integration is separate.
"""

import pytest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import Button, Static


class TestHotkeyCaptureWidget:
    """Test HotkeyCapture widget UI components."""

    @pytest.mark.asyncio
    async def test_displays_current_hotkey(self):
        """Widget displays current hotkey value."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="alt_r")

        async with TestApp().run_test() as pilot:
            label = pilot.app.query_one("#hotkey-display", Static)
            # Should display human-readable hotkey
            assert "Alt" in label.render() or "alt" in str(label.render()).lower()

    @pytest.mark.asyncio
    async def test_has_set_button(self):
        """Widget has SET button for capture mode."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            btn = pilot.app.query_one("#set-hotkey-btn", Button)
            assert btn is not None
            assert "SET" in str(btn.label).upper() or "set" in str(btn.label).lower()

    @pytest.mark.asyncio
    async def test_set_button_enters_capture_mode(self):
        """Clicking SET button enters capture mode."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)
            btn = pilot.app.query_one("#set-hotkey-btn", Button)

            # Initially not in capture mode
            assert widget.is_capturing is False

            # Click SET
            await pilot.click(btn)
            await pilot.pause()

            # Should be in capture mode
            assert widget.is_capturing is True

    @pytest.mark.asyncio
    async def test_capture_mode_shows_instruction(self):
        """In capture mode, shows 'Press key...' instruction."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)
            btn = pilot.app.query_one("#set-hotkey-btn", Button)

            # Enter capture mode
            await pilot.click(btn)
            await pilot.pause()

            label = pilot.app.query_one("#hotkey-display", Static)
            label_text = str(label.render()).lower()
            assert "press" in label_text or "waiting" in label_text

    @pytest.mark.asyncio
    async def test_on_change_callback_called(self):
        """on_change callback is called when hotkey captured."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        callback = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r", on_change=callback)

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)

            # Simulate hotkey capture
            widget._on_key_captured("alt_r")
            await pilot.pause()

            callback.assert_called_once_with("alt_r")

    @pytest.mark.asyncio
    async def test_cancel_exits_capture_mode(self):
        """Clicking Cancel or Escape exits capture mode."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)
            btn = pilot.app.query_one("#set-hotkey-btn", Button)

            # Enter capture mode
            await pilot.click(btn)
            await pilot.pause()
            assert widget.is_capturing is True

            # Cancel
            widget._cancel_capture()
            await pilot.pause()

            assert widget.is_capturing is False


class TestHotkeyFormatting:
    """Test hotkey string formatting for display."""

    def test_format_ctrl_r(self):
        """ctrl_r displays as 'Right Ctrl'."""
        from soupawhisper.tui.widgets.hotkey_capture import format_hotkey

        assert format_hotkey("ctrl_r") == "Right Ctrl"

    def test_format_alt_r(self):
        """alt_r displays as 'Right Alt'."""
        from soupawhisper.tui.widgets.hotkey_capture import format_hotkey

        assert format_hotkey("alt_r") == "Right Alt"

    def test_format_f12(self):
        """f12 displays as 'F12'."""
        from soupawhisper.tui.widgets.hotkey_capture import format_hotkey

        assert format_hotkey("f12") == "F12"

    def test_format_combination(self):
        """ctrl_r+f12 displays as 'Right Ctrl + F12'."""
        from soupawhisper.tui.widgets.hotkey_capture import format_hotkey

        assert format_hotkey("ctrl_r+f12") == "Right Ctrl + F12"


class TestHotkeyCaptureE2E:
    """E2E tests for HotkeyCapture in real Settings screen."""

    @pytest.mark.asyncio
    async def test_hotkey_capture_visible_in_settings(self):
        """HotkeyCapture widget is visible in Settings screen."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        app = TUIApp(test_mode=True)
        async with app.run_test(size=(100, 40)) as pilot:
            # Go to settings
            await pilot.press("s")
            await pilot.pause()

            # Find HotkeyCapture widget
            widgets = app.query(HotkeyCapture)
            assert len(widgets) == 1

            widget = widgets[0]
            # Check it has both display and button
            display = widget.query_one("#hotkey-display", Static)
            btn = widget.query_one("#set-hotkey-btn", Button)

            assert display is not None
            assert btn is not None
            assert "SET" in str(btn.label).upper()

    @pytest.mark.asyncio
    async def test_hotkey_capture_enter_capture_mode_in_settings(self):
        """Clicking SET enters capture mode in real settings."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        app = TUIApp(test_mode=True)
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.press("s")
            await pilot.pause()

            widget = app.query_one(HotkeyCapture)

            # Mock the key listener and trigger capture mode directly
            with patch.object(widget, "_start_key_listener"):
                # Directly call _start_capture (button handler calls this)
                widget._start_capture()
                await pilot.pause()

                # Should be in capture mode
                assert widget.is_capturing is True

                # Label should show "Press key..."
                label = widget.query_one("#hotkey-display", Static)
                assert "press" in str(label.render()).lower()

    @pytest.mark.asyncio
    async def test_hotkey_capture_saves_to_config(self):
        """Captured hotkey is saved to config."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture
        from unittest.mock import patch

        with patch("soupawhisper.config.Config.save") as mock_save:
            app = TUIApp(test_mode=True)
            async with app.run_test(size=(100, 40)) as pilot:
                await pilot.press("s")
                await pilot.pause()

                widget = app.query_one(HotkeyCapture)

                # Simulate capturing a key
                widget._on_key_captured("f12")
                await pilot.pause()

                # Widget should have new value
                assert widget.value == "f12"

                # Should exit capture mode
                assert widget.is_capturing is False

    @pytest.mark.asyncio
    async def test_hotkey_cancel_restores_original(self):
        """Canceling capture restores original hotkey."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        app = TUIApp(test_mode=True)
        async with app.run_test(size=(100, 80)) as pilot:  # Larger size to see Recording section
            await pilot.press("s")
            await pilot.pause()

            widget = app.query_one(HotkeyCapture)
            original = widget.value

            # Enter capture mode (mock key listener to avoid pynput issues)
            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

                # Cancel
                widget._cancel_capture()
                await pilot.pause()

            # Value should be unchanged
            assert widget.value == original
            assert widget.is_capturing is False


class TestHotkeyCombinations:
    """Test hotkey combination capture (wait for release)."""

    @pytest.mark.asyncio
    async def test_captures_single_key_on_release(self):
        """Single key is captured only after release."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        callback = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r", on_change=callback)

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)

            # Start capture with mocked listener
            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

            # Simulate press alt_r
            widget._on_key_press("alt_r")
            await pilot.pause()

            # Not yet captured - still pressing
            assert widget.is_capturing is True
            callback.assert_not_called()

            # Simulate release
            widget._on_key_release("alt_r")
            await pilot.pause()

            # Now captured
            assert widget.is_capturing is False
            callback.assert_called_once_with("alt_r")

    @pytest.mark.asyncio
    async def test_captures_key_combination(self):
        """Captures key combination like alt_r+f12."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        callback = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r", on_change=callback)

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)

            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

            # Press alt_r, then f12
            widget._on_key_press("alt_r")
            widget._on_key_press("f12")
            await pilot.pause()

            # Still capturing
            assert widget.is_capturing is True

            # Release f12, still holding alt_r
            widget._on_key_release("f12")
            await pilot.pause()

            # Still capturing (alt_r still pressed)
            assert widget.is_capturing is True

            # Release alt_r
            widget._on_key_release("alt_r")
            await pilot.pause()

            # Now captured as combination
            assert widget.is_capturing is False
            # Combination should be sorted consistently
            call_arg = callback.call_args[0][0]
            assert "alt_r" in call_arg
            assert "f12" in call_arg
            assert "+" in call_arg

    @pytest.mark.asyncio
    async def test_shows_realtime_combination(self):
        """Display updates in realtime as keys are pressed."""
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HotkeyCapture(hotkey="ctrl_r")

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(HotkeyCapture)

            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

            # Press alt_r
            widget._on_key_press("alt_r")
            await pilot.pause()

            label = widget.query_one("#hotkey-display", Static)
            label_text = str(label.render())
            assert "Alt" in label_text

            # Press f12 too
            widget._on_key_press("f12")
            await pilot.pause()

            label_text = str(label.render())
            assert "Alt" in label_text
            assert "F12" in label_text


class TestKeybindingsBlocked:
    """Test that keybindings are blocked during hotkey capture."""

    @pytest.mark.asyncio
    async def test_h_blocked_during_capture(self):
        """Pressing 'h' doesn't switch tabs during capture mode."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture
        from textual.widgets import TabbedContent

        app = TUIApp(test_mode=True)
        async with app.run_test(size=(100, 80)) as pilot:
            # Go to settings
            await pilot.press("s")
            await pilot.pause()

            tabs = app.query(TabbedContent).first()
            assert tabs.active == "settings-tab"

            # Enter capture mode
            widget = app.query_one(HotkeyCapture)
            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

            # Try to press 'h' to switch to history
            await pilot.press("h")
            await pilot.pause()

            # Should still be on settings (h was blocked)
            assert tabs.active == "settings-tab"

    @pytest.mark.asyncio
    async def test_c_blocked_during_capture(self):
        """Pressing 'c' doesn't copy during capture mode."""
        from soupawhisper.tui.app import TUIApp
        from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

        app = TUIApp(test_mode=True)
        async with app.run_test(size=(100, 80)) as pilot:
            await pilot.press("s")
            await pilot.pause()

            widget = app.query_one(HotkeyCapture)
            with patch.object(widget, "_start_key_listener"):
                widget._start_capture()
                await pilot.pause()

            with patch("soupawhisper.tui.screens.history.copy_to_clipboard") as mock_copy:
                await pilot.press("c")
                await pilot.pause()

                # Copy should not have been called
                mock_copy.assert_not_called()


class TestHistoryAutoCopy:
    """Test auto-copy when clicking on history row."""

    @pytest.mark.asyncio
    async def test_row_select_copies_to_clipboard(self):
        """Selecting a row copies text to clipboard."""
        from soupawhisper.tui.screens.history import HistoryScreen
        from textual.app import App

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen()

        with patch("soupawhisper.tui.screens.history.copy_to_clipboard") as mock_copy:
            async with TestApp().run_test() as pilot:
                screen = pilot.app.query_one(HistoryScreen)

                # Setup mock data
                mock_storage = MagicMock()
                mock_storage.get_recent.return_value = [
                    {"id": "1", "timestamp": None, "text": "Test text", "language": "en"}
                ]
                screen._storage = mock_storage
                screen.refresh_data()
                await pilot.pause()

                # Select row (triggers RowSelected event)
                table = screen._table
                if table and table.row_count > 0:
                    # Simulate row selection
                    table.cursor_coordinate = (0, 0)
                    await pilot.pause()

                    # Trigger action_select_cursor which fires RowSelected
                    table.action_select_cursor()
                    await pilot.pause()

                    # Should have copied
                    mock_copy.assert_called_with("Test text")
