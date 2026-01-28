"""Edge case tests for TUI components.

TDD: Tests for boundary conditions and error paths.
"""

from unittest.mock import MagicMock

import pytest
from textual.app import App, ComposeResult


class TestHistoryScreenEdgeCases:
    """Edge case tests for HistoryScreen."""

    @pytest.mark.asyncio
    async def test_copy_selected_when_table_is_none(self):
        """copy_selected handles None table gracefully."""
        from soupawhisper.tui.screens.history import HistoryScreen

        screen = HistoryScreen(history_storage=None)
        screen._table = None
        # Should not raise
        screen.copy_selected()

    @pytest.mark.asyncio
    async def test_copy_selected_with_empty_entries(self):
        """copy_selected handles empty entries list."""
        from soupawhisper.tui.screens.history import HistoryScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=None)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(HistoryScreen)
            screen._entries = []
            # Should not raise
            screen.copy_selected()

    @pytest.mark.asyncio
    async def test_refresh_data_with_none_storage(self):
        """refresh_data handles None storage gracefully."""
        from soupawhisper.tui.screens.history import HistoryScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=None)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(HistoryScreen)
            # Should not raise
            screen.refresh_data()
            assert screen._entries == []

    def test_format_time_with_none_timestamp(self):
        """_format_time handles None timestamp."""
        from soupawhisper.tui.screens.history import HistoryScreen

        screen = HistoryScreen(history_storage=None)
        result = screen._format_time(None)
        assert result == ""

    def test_truncate_text_with_empty_string(self):
        """_truncate_text handles empty string."""
        from soupawhisper.tui.screens.history import HistoryScreen

        screen = HistoryScreen(history_storage=None)
        result = screen._truncate_text("")
        assert result == ""

    def test_truncate_text_exact_length(self):
        """_truncate_text handles text exactly at max length."""
        from soupawhisper.tui.screens.history import HistoryScreen

        screen = HistoryScreen(history_storage=None)
        text = "a" * 80
        result = screen._truncate_text(text, max_length=80)
        assert result == text
        assert len(result) == 80


class TestSettingsScreenEdgeCases:
    """Edge case tests for SettingsScreen."""

    @pytest.mark.asyncio
    async def test_get_config_with_none_config(self):
        """_get_config returns default when config is None."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        screen = SettingsScreen(config=None)
        result = screen._get_config("api_key", "default_value")
        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_on_field_changed_with_none_callback(self):
        """_on_field_changed handles None callback gracefully."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        screen = SettingsScreen(config=MagicMock(), on_save=None)
        # Should not raise
        screen._on_field_changed("test_field", "test_value")


class TestStatusBarEdgeCases:
    """Edge case tests for StatusBar."""

    @pytest.mark.asyncio
    async def test_render_with_empty_error_message(self):
        """StatusBar renders correctly with empty error message."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar(hotkey="Ctrl+R")

        async with TestApp().run_test() as pilot:
            status_bar = pilot.app.query_one(StatusBar)
            status_bar.error_message = ""
            await pilot.pause()

            rendered = status_bar.render()
            assert "Ready" in rendered

    @pytest.mark.asyncio
    async def test_simultaneous_recording_and_transcribing(self):
        """StatusBar handles simultaneous states (recording takes priority)."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar(hotkey="Ctrl+R")

        async with TestApp().run_test() as pilot:
            status_bar = pilot.app.query_one(StatusBar)
            status_bar.is_recording = True
            status_bar.is_transcribing = True
            await pilot.pause()

            rendered = status_bar.render()
            # Recording should take priority
            assert "REC" in rendered


class TestWorkerControllerEdgeCases:
    """Edge case tests for WorkerController."""

    def test_wrap_with_none_callback(self):
        """_wrap returns None for None callback."""
        from soupawhisper.tui.worker_controller import WorkerController

        controller = WorkerController(
            config=MagicMock(),
            call_from_thread=MagicMock(),
        )
        result = controller._wrap(None)
        assert result is None

    def test_stop_when_not_started(self):
        """stop handles case when worker was never started."""
        from soupawhisper.tui.worker_controller import WorkerController

        controller = WorkerController(
            config=MagicMock(),
            call_from_thread=MagicMock(),
        )
        # Should not raise
        controller.stop()


class TestHotkeyInputEdgeCases:
    """Edge case tests for HotkeyInput."""

    def test_parse_hotkey_with_only_plus(self):
        """_parse_hotkey handles string with only plus sign."""
        from soupawhisper.tui.widgets.hotkey_input import HotkeyInput

        widget = HotkeyInput(hotkey="+")
        # Should default to ctrl_r
        assert widget._modifier == "ctrl_r"

    def test_value_after_internal_state_change(self):
        """value property reflects internal state changes."""
        from soupawhisper.tui.widgets.hotkey_input import HotkeyInput

        widget = HotkeyInput(hotkey="ctrl_r")
        widget._modifier = "alt_l"
        widget._key = "f10"
        widget._notify_change()

        assert widget.value == "alt_l+f10"
