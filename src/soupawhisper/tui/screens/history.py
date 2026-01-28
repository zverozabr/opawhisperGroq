"""History screen for displaying transcription history.

Single Responsibility: Display and manage transcription history.
"""

from datetime import datetime
from typing import Optional

from textual.containers import Container
from textual.widgets import DataTable

from soupawhisper.clipboard import copy_to_clipboard


class HistoryScreen(Container):
    """Screen displaying transcription history.

    Shows a table of recent transcriptions with:
    - Time (HH:MM)
    - Text (truncated)
    - Language code

    Supports:
    - Copying selected entry to clipboard
    - Refreshing data
    """

    DEFAULT_CSS = """
    HistoryScreen {
        width: 100%;
        height: 100%;
    }

    HistoryScreen DataTable {
        width: 100%;
        height: 100%;
    }

    HistoryScreen .empty-message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: $text-muted;
    }
    """

    def __init__(self, history_storage=None, history_days: int = 3, **kwargs):
        """Initialize history screen.

        Args:
            history_storage: HistoryStorage instance (or mock for testing).
            history_days: Number of days to show history for.
        """
        super().__init__(**kwargs)
        self._storage = history_storage
        self._history_days = history_days
        self._entries = []
        self._table: Optional[DataTable] = None

    def compose(self):
        """Create child widgets."""
        self._table = DataTable(cursor_type="row")
        yield self._table

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        if self._table:
            self._table.add_column("Time", width=6, key="time")
            self._table.add_column("Text", key="text")
            self._table.add_column("Lang", width=4, key="lang")
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh history data from storage."""
        if not self._table:
            return

        # Clear existing rows
        self._table.clear()

        # Get entries from storage
        if self._storage:
            self._entries = self._storage.get_recent(days=self._history_days)
        else:
            self._entries = []

        # Add rows - handle both dict (mock) and HistoryEntry (real) objects
        for entry in self._entries:
            if hasattr(entry, "timestamp"):
                # HistoryEntry object
                time_str = self._format_time(entry.timestamp)
                text = self._truncate_text(entry.text)
                lang = entry.language
                entry_id = str(entry.id)
            else:
                # Dict (from mock in tests)
                time_str = self._format_time(entry.get("timestamp"))
                text = self._truncate_text(entry.get("text", ""))
                lang = entry.get("language", "")
                entry_id = str(entry.get("id", ""))

            self._table.add_row(time_str, text, lang, key=entry_id)

    def copy_selected(self) -> None:
        """Copy selected entry text to clipboard."""
        if not self._table or not self._entries:
            return

        # Get selected row
        cursor_row = self._table.cursor_row
        if cursor_row is not None and 0 <= cursor_row < len(self._entries):
            entry = self._entries[cursor_row]
            # Handle both dict (mock) and HistoryEntry (real) objects
            if hasattr(entry, "text"):
                text = entry.text
            else:
                text = entry.get("text", "")
            if text:
                copy_to_clipboard(text)

    def _format_time(self, timestamp) -> str:
        """Format timestamp as HH:MM.

        Args:
            timestamp: datetime object or None.

        Returns:
            Formatted time string.
        """
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%H:%M")
        return ""

    def _truncate_text(self, text: str, max_length: int = 80) -> str:
        """Truncate text to max length.

        Args:
            text: Text to truncate.
            max_length: Maximum length.

        Returns:
            Truncated text with ellipsis if needed.
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
