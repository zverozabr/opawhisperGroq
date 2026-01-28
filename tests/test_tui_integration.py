"""Integration tests for TUI.

Tests the full TUI workflow with mocked worker.
Fixtures: mock_config, tui_app_patched from conftest.py
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestTUIIntegrationRecording:
    """Test TUI recording workflow integration."""

    @pytest.mark.asyncio
    async def test_recording_updates_status_bar(self, tui_app_patched):
        """Recording callback updates StatusBar state."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_patched.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Initially not recording
            assert not status_bar.is_recording

            # Simulate recording start
            app.on_recording_changed(True)
            await pilot.pause()

            assert status_bar.is_recording
            assert status_bar.has_class("recording")

            # Simulate recording stop
            app.on_recording_changed(False)
            await pilot.pause()

            assert not status_bar.is_recording
            assert not status_bar.has_class("recording")

    @pytest.mark.asyncio
    async def test_transcribing_updates_status_bar(self, tui_app_patched):
        """Transcribing callback updates StatusBar state."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_patched.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate transcription start
            app.on_transcribing_changed(True)
            await pilot.pause()

            assert status_bar.is_transcribing
            assert status_bar.has_class("transcribing")

            # Simulate transcription end
            app.on_transcribing_changed(False)
            await pilot.pause()

            assert not status_bar.is_transcribing


class TestTUIIntegrationTranscription:
    """Test TUI transcription workflow integration."""

    @pytest.mark.asyncio
    async def test_transcription_adds_to_history(self, tui_app_patched):
        """Transcription callback adds entry to history storage."""
        async with tui_app_patched.run_test() as pilot:
            app = pilot.app

            # Mock history storage
            mock_history = MagicMock()
            app.history = mock_history
            app.config.history_enabled = True

            # Simulate transcription complete
            app.on_transcription_complete("Hello world", "en")
            await pilot.pause()

            # Should have added to history
            mock_history.add.assert_called_once_with("Hello world", "en")

    @pytest.mark.asyncio
    async def test_transcription_respects_history_disabled(self, tui_app_patched):
        """Transcription doesn't add to history when disabled."""
        async with tui_app_patched.run_test() as pilot:
            app = pilot.app

            mock_history = MagicMock()
            app.history = mock_history
            app.config.history_enabled = False

            app.on_transcription_complete("Hello world", "en")
            await pilot.pause()

            mock_history.add.assert_not_called()


class TestTUIIntegrationSettings:
    """Test TUI settings workflow integration."""

    @pytest.mark.asyncio
    async def test_settings_change_saves_config(self, tui_app_patched):
        """Changing settings saves config to file."""
        async with tui_app_patched.run_test() as pilot:
            app = pilot.app

            # Simulate field change
            app._save_field("auto_type", False)
            await pilot.pause()

            # Config should be updated
            assert app.config.auto_type is False


class TestTUIIntegrationError:
    """Test TUI error handling integration."""

    @pytest.mark.asyncio
    async def test_error_updates_status_bar(self, tui_app_patched):
        """Error callback updates StatusBar with error message."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_patched.run_test() as pilot:
            app = pilot.app
            status_bar = app.query_one(StatusBar)

            # Simulate error
            app.on_error("Permission denied")
            await pilot.pause()

            assert status_bar.error_message == "Permission denied"
            assert status_bar.has_class("error")


class TestTUIIntegrationNavigation:
    """Test TUI navigation integration."""

    @pytest.mark.asyncio
    async def test_tab_navigation_works(self, tui_app_patched):
        """Tab navigation using keybindings works correctly."""
        from textual.widgets import TabbedContent

        async with tui_app_patched.run_test() as pilot:
            tabs = pilot.app.query_one(TabbedContent)

            # Start on history
            assert tabs.active == "history-tab"

            # Navigate to settings
            await pilot.press("s")
            await pilot.pause()
            assert tabs.active == "settings-tab"

            # Navigate back to history
            await pilot.press("h")
            await pilot.pause()
            assert tabs.active == "history-tab"

    @pytest.mark.asyncio
    async def test_quit_action_exits_app(self, tui_app_patched):
        """Pressing Ctrl+C exits the application."""
        async with tui_app_patched.run_test() as pilot:
            await pilot.press("ctrl+c")
            await pilot.pause()

            assert tui_app_patched._exit


class TestTUIIntegrationCopy:
    """Test TUI copy functionality integration."""

    @pytest.mark.asyncio
    async def test_copy_action_copies_selected_text(self, tui_app_patched):
        """Copy action copies selected history entry."""
        from soupawhisper.tui.screens.history import HistoryScreen

        with patch("soupawhisper.tui.screens.history.copy_to_clipboard") as mock_copy:
            async with tui_app_patched.run_test() as pilot:
                app = pilot.app
                history_screen = app.query_one(HistoryScreen)

                # Add mock data
                mock_storage = MagicMock()
                mock_storage.get_recent.return_value = [
                    {"id": "1", "text": "Copy this text", "language": "en", "timestamp": datetime.now()},
                ]
                history_screen._storage = mock_storage
                history_screen.refresh_data()
                await pilot.pause()

                # Select and copy
                table = history_screen._table
                table.cursor_coordinate = (0, 0)
                await pilot.pause()

                await pilot.press("c")
                await pilot.pause()

                mock_copy.assert_called_once_with("Copy this text")
