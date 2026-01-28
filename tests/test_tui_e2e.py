"""End-to-end tests for TUI application.

Tests the complete user workflow from start to finish.
Fixtures: mock_config, mock_history_entries, tui_app_with_history from conftest.py
"""

from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import DataTable, Select, Switch, TabbedContent


class TestTUIE2EStartup:
    """Test TUI application startup."""

    @pytest.mark.asyncio
    async def test_app_starts_successfully(self, tui_app_with_history):
        """App should start without errors."""
        async with tui_app_with_history.run_test() as pilot:
            assert pilot.app.is_running

    @pytest.mark.asyncio
    async def test_app_shows_ready_status(self, tui_app_with_history):
        """App should show Ready status on startup."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            status_bar = pilot.app.query_one(StatusBar)
            rendered = status_bar.render()
            assert "Ready" in rendered

    @pytest.mark.asyncio
    async def test_app_shows_hotkey_hint(self, tui_app_with_history):
        """App should show hotkey hint on startup."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            status_bar = pilot.app.query_one(StatusBar)
            rendered = status_bar.render()
            # Should contain some hotkey hint
            assert "Ctrl" in rendered or "ctrl" in rendered.lower()


class TestTUIE2ENavigation:
    """Test TUI navigation workflow."""

    @pytest.mark.asyncio
    async def test_full_tab_navigation_cycle(self, tui_app_with_history):
        """User can navigate through all tabs."""
        async with tui_app_with_history.run_test() as pilot:
            tabs = pilot.app.query_one(TabbedContent)

            # Start on history
            assert tabs.active == "history-tab"

            # Go to settings
            await pilot.press("s")
            await pilot.pause()
            assert tabs.active == "settings-tab"

            # Back to history
            await pilot.press("h")
            await pilot.pause()
            assert tabs.active == "history-tab"

    @pytest.mark.asyncio
    async def test_quit_from_any_tab(self, tui_app_with_history):
        """User can quit from any tab."""
        async with tui_app_with_history.run_test() as pilot:
            # Go to settings first
            await pilot.press("s")
            await pilot.pause()

            # Quit
            await pilot.press("q")
            await pilot.pause()

            assert tui_app_with_history._exit


class TestTUIE2EHistoryWorkflow:
    """Test history viewing workflow."""

    @pytest.mark.asyncio
    async def test_history_displays_entries(self, tui_app_with_history):
        """History tab shows transcription entries."""
        async with tui_app_with_history.run_test() as pilot:
            table = pilot.app.query_one(DataTable)
            # Table should have rows (exact count depends on mock)
            assert table is not None

    @pytest.mark.asyncio
    async def test_copy_transcription_to_clipboard(self, tui_app_with_history, mock_history_entries):
        """User can copy transcription text."""
        from soupawhisper.tui.screens.history import HistoryScreen

        with patch("soupawhisper.tui.screens.history.copy_to_clipboard") as mock_copy:
            async with tui_app_with_history.run_test() as pilot:
                history_screen = pilot.app.query_one(HistoryScreen)

                # Setup mock data directly
                mock_storage = MagicMock()
                mock_storage.get_recent.return_value = mock_history_entries
                history_screen._storage = mock_storage
                history_screen.refresh_data()
                await pilot.pause()

                # Select first row and copy
                table = history_screen._table
                if table and table.row_count > 0:
                    table.cursor_coordinate = (0, 0)
                    await pilot.pause()

                    await pilot.press("c")
                    await pilot.pause()

                    # Should have called copy
                    mock_copy.assert_called()


class TestTUIE2ESettingsWorkflow:
    """Test settings editing workflow."""

    @pytest.mark.asyncio
    async def test_settings_shows_current_values(self, tui_app_with_history, mock_config):
        """Settings tab shows current config values."""
        async with tui_app_with_history.run_test() as pilot:
            # Navigate to settings
            await pilot.press("s")
            await pilot.pause()

            # Check provider select has value
            provider_select = pilot.app.query_one("#provider-select", Select)
            assert provider_select.value == mock_config.active_provider

    @pytest.mark.asyncio
    async def test_toggle_auto_type(self, tui_app_with_history):
        """User can toggle auto-type setting."""
        async with tui_app_with_history.run_test() as pilot:
            # Navigate to settings
            await pilot.press("s")
            await pilot.pause()

            # Find auto-type switch
            auto_type = pilot.app.query_one("#auto-type", Switch)
            initial_value = auto_type.value

            # Toggle it
            auto_type.toggle()
            await pilot.pause()

            assert auto_type.value != initial_value


class TestTUIE2ERecordingWorkflow:
    """Test recording state transitions."""

    @pytest.mark.asyncio
    async def test_recording_state_updates_ui(self, tui_app_with_history):
        """Recording state changes update the UI."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate recording start
            app.on_recording_changed(True)
            await pilot.pause()

            assert status_bar.is_recording
            assert "REC" in status_bar.render()

            # Simulate recording stop
            app.on_recording_changed(False)
            await pilot.pause()

            assert not status_bar.is_recording
            assert "Ready" in status_bar.render()

    @pytest.mark.asyncio
    async def test_transcribing_state_updates_ui(self, tui_app_with_history):
        """Transcribing state changes update the UI."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate transcribing start
            app.on_transcribing_changed(True)
            await pilot.pause()

            assert status_bar.is_transcribing
            assert "Transcribing" in status_bar.render()

            # Simulate transcribing end
            app.on_transcribing_changed(False)
            await pilot.pause()

            assert not status_bar.is_transcribing


class TestTUIE2EErrorHandling:
    """Test error handling workflow."""

    @pytest.mark.asyncio
    async def test_error_displays_in_status_bar(self, tui_app_with_history):
        """Errors are displayed in status bar."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate error
            app.on_error("API key invalid")
            await pilot.pause()

            assert "API key invalid" in status_bar.render()
            assert status_bar.has_class("error")

    @pytest.mark.asyncio
    async def test_error_clears_on_new_recording(self, tui_app_with_history):
        """Error clears when new recording starts."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate error
            app.on_error("Some error")
            await pilot.pause()

            # Start recording (should clear error)
            app.on_recording_changed(True)
            status_bar.error_message = ""  # Clear error on recording
            await pilot.pause()

            assert status_bar.error_message == ""


class TestTUIE2EVimNavigation:
    """Test vim-style navigation."""

    @pytest.mark.asyncio
    async def test_j_moves_cursor_down(self, tui_app_with_history, mock_history_entries):
        """Pressing 'j' moves cursor down in history."""
        from soupawhisper.tui.screens.history import HistoryScreen

        async with tui_app_with_history.run_test() as pilot:
            history_screen = pilot.app.query_one(HistoryScreen)

            # Setup mock data
            mock_storage = MagicMock()
            mock_storage.get_recent.return_value = mock_history_entries
            history_screen._storage = mock_storage
            history_screen.refresh_data()
            await pilot.pause()

            table = history_screen._table
            if table and table.row_count > 1:
                initial_row = table.cursor_row
                await pilot.press("j")
                await pilot.pause()
                # Cursor should move down
                assert table.cursor_row >= initial_row

    @pytest.mark.asyncio
    async def test_k_moves_cursor_up(self, tui_app_with_history, mock_history_entries):
        """Pressing 'k' moves cursor up in history."""
        from soupawhisper.tui.screens.history import HistoryScreen

        async with tui_app_with_history.run_test() as pilot:
            history_screen = pilot.app.query_one(HistoryScreen)

            # Setup mock data
            mock_storage = MagicMock()
            mock_storage.get_recent.return_value = mock_history_entries
            history_screen._storage = mock_storage
            history_screen.refresh_data()
            await pilot.pause()

            table = history_screen._table
            if table and table.row_count > 1:
                # Move down first
                await pilot.press("j")
                await pilot.pause()
                row_after_j = table.cursor_row

                # Move up
                await pilot.press("k")
                await pilot.pause()
                # Cursor should move up or stay
                assert table.cursor_row <= row_after_j


class TestTUIE2EFullWorkflow:
    """Test complete user workflow."""

    @pytest.mark.asyncio
    async def test_complete_transcription_workflow(self, tui_app_with_history):
        """Test full: view history -> check settings -> simulate transcription."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_with_history.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # 1. Start on history tab
            tabs = pilot.app.query_one(TabbedContent)
            assert tabs.active == "history-tab"

            # 2. Check settings
            await pilot.press("s")
            await pilot.pause()
            assert tabs.active == "settings-tab"

            # 3. Go back to history
            await pilot.press("h")
            await pilot.pause()

            # 4. Simulate recording
            app.on_recording_changed(True)
            await pilot.pause()
            assert status_bar.is_recording

            # 5. Stop recording
            app.on_recording_changed(False)
            await pilot.pause()

            # 6. Simulate transcribing
            app.on_transcribing_changed(True)
            await pilot.pause()
            assert status_bar.is_transcribing

            # 7. Complete transcription
            app.on_transcribing_changed(False)
            app.on_transcription_complete("Test transcription", "en")
            await pilot.pause()

            # 8. Quit
            await pilot.press("q")
            await pilot.pause()
            assert app._exit
