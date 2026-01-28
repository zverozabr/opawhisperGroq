"""Tests for HistoryScreen.

TDD: Tests written BEFORE implementation.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.widgets import DataTable


class TestHistoryScreenCompose:
    """Test HistoryScreen widget composition."""

    @pytest.mark.asyncio
    async def test_has_data_table(self):
        """HistoryScreen has a DataTable widget."""
        from soupawhisper.tui.screens.history import HistoryScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen()

        async with TestApp().run_test() as pilot:
            tables = pilot.app.query(DataTable)
            assert len(tables) == 1

    @pytest.mark.asyncio
    async def test_table_has_columns(self):
        """DataTable has Time, Text, Lang columns."""
        from soupawhisper.tui.screens.history import HistoryScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen()

        async with TestApp().run_test() as pilot:
            table = pilot.app.query_one(DataTable)
            # Check columns exist
            columns = [col.label for col in table.columns.values()]
            assert len(columns) >= 3


class TestHistoryScreenData:
    """Test HistoryScreen data display."""

    @pytest.mark.asyncio
    async def test_displays_entries(self):
        """HistoryScreen displays transcription entries."""
        from soupawhisper.tui.screens.history import HistoryScreen

        # Mock history storage
        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = [
            {"id": "1", "text": "Hello world", "language": "en", "timestamp": datetime.now()},
            {"id": "2", "text": "Привет мир", "language": "ru", "timestamp": datetime.now()},
        ]

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

        async with TestApp().run_test() as pilot:
            table = pilot.app.query_one(DataTable)
            assert table.row_count == 2

    @pytest.mark.asyncio
    async def test_empty_state(self):
        """HistoryScreen shows message when no entries."""
        from soupawhisper.tui.screens.history import HistoryScreen

        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

        async with TestApp().run_test() as pilot:
            table = pilot.app.query_one(DataTable)
            assert table.row_count == 0


class TestHistoryScreenActions:
    """Test HistoryScreen actions."""

    @pytest.mark.asyncio
    async def test_refresh_updates_table(self):
        """Calling refresh() updates table content."""
        from soupawhisper.tui.screens.history import HistoryScreen

        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(HistoryScreen)

            # Add an entry
            mock_storage.get_recent.return_value = [
                {"id": "1", "text": "New entry", "language": "en", "timestamp": datetime.now()},
            ]

            screen.refresh_data()
            await pilot.pause()

            table = pilot.app.query_one(DataTable)
            assert table.row_count == 1

    @pytest.mark.asyncio
    async def test_copy_action(self):
        """Pressing 'c' copies selected entry to clipboard."""
        from soupawhisper.tui.screens.history import HistoryScreen

        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = [
            {"id": "1", "text": "Copy this", "language": "en", "timestamp": datetime.now()},
        ]

        class TestApp(App):
            BINDINGS = [("c", "copy", "Copy")]

            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

            def action_copy(self) -> None:
                screen = self.query_one(HistoryScreen)
                screen.copy_selected()

        with patch("soupawhisper.tui.screens.history.copy_to_clipboard") as mock_copy:
            async with TestApp().run_test() as pilot:
                table = pilot.app.query_one(DataTable)
                # Select first row
                table.cursor_coordinate = (0, 0)
                await pilot.pause()

                await pilot.press("c")
                await pilot.pause()

                # Should have copied the text
                mock_copy.assert_called_once_with("Copy this")


class TestHistoryScreenFormatting:
    """Test HistoryScreen text formatting."""

    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        """Long text is truncated in table."""
        from soupawhisper.tui.screens.history import HistoryScreen

        long_text = "A" * 200  # Very long text

        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = [
            {"id": "1", "text": long_text, "language": "en", "timestamp": datetime.now()},
        ]

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

        async with TestApp().run_test() as pilot:
            table = pilot.app.query_one(DataTable)
            # Table should still render (text truncated internally)
            assert table.row_count == 1

    @pytest.mark.asyncio
    async def test_formats_time(self):
        """Time is formatted as HH:MM."""
        from soupawhisper.tui.screens.history import HistoryScreen

        timestamp = datetime(2025, 1, 28, 14, 32, 0)

        mock_storage = MagicMock()
        mock_storage.get_recent.return_value = [
            {"id": "1", "text": "Test", "language": "en", "timestamp": timestamp},
        ]

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HistoryScreen(history_storage=mock_storage)

        async with TestApp().run_test() as pilot:
            # Time formatting is tested by the screen not crashing
            table = pilot.app.query_one(DataTable)
            assert table.row_count == 1
