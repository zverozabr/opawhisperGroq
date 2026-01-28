"""History storage using Markdown file."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from soupawhisper.constants import HISTORY_PATH, ensure_dir


@dataclass
class HistoryEntry:
    """Single transcription history entry."""

    id: int
    text: str
    language: str
    timestamp: datetime

    @property
    def time_str(self) -> str:
        """Format timestamp as HH:MM."""
        return self.timestamp.strftime("%H:%M")

    @property
    def date_str(self) -> str:
        """Format timestamp as YYYY-MM-DD."""
        return self.timestamp.strftime("%Y-%m-%d")


class HistoryStorage:
    """Markdown file-based history storage for transcriptions."""

    # Entry format: ## YYYY-MM-DD HH:MM | lang\ntext\n
    ENTRY_PATTERN = re.compile(
        r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w*)\n(.+?)(?=\n## |\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def __init__(self, file_path: Optional[Path] = None):
        """Initialize history storage.

        Args:
            file_path: Path to Markdown file. Defaults to ~/.config/soupawhisper/history.md
        """
        self.file_path = file_path or HISTORY_PATH
        ensure_dir(self.file_path.parent)
        self._next_id = 1
        self._entries: list[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        """Load entries from Markdown file."""
        if not self.file_path.exists():
            return

        content = self.file_path.read_text(encoding="utf-8")
        self._entries = []

        for match in self.ENTRY_PATTERN.finditer(content):
            timestamp_str, language, text = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            self._entries.append(
                HistoryEntry(
                    id=self._next_id,
                    text=text.strip(),
                    language=language,
                    timestamp=timestamp,
                )
            )
            self._next_id += 1

        # Sort by timestamp descending (newest first)
        self._entries.sort(key=lambda e: e.timestamp, reverse=True)

    def _save(self) -> None:
        """Save entries to Markdown file."""
        # Sort by timestamp ascending for file (oldest first, newest at end)
        sorted_entries = sorted(self._entries, key=lambda e: e.timestamp)

        lines = ["# SoupaWhisper History\n\n"]
        for entry in sorted_entries:
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"## {timestamp_str} | {entry.language}\n")
            lines.append(f"{entry.text}\n\n")

        self.file_path.write_text("".join(lines), encoding="utf-8")

    def add(self, text: str, language: str = "") -> int:
        """Add new transcription to history.

        Args:
            text: Transcribed text
            language: Detected/specified language

        Returns:
            ID of the new entry
        """
        entry = HistoryEntry(
            id=self._next_id,
            text=text,
            language=language,
            timestamp=datetime.now(),
        )
        self._next_id += 1
        self._entries.insert(0, entry)  # Add to front (newest first)
        self._save()
        return entry.id

    def get_recent(self, days: int = 3) -> list[HistoryEntry]:
        """Get recent history entries.

        Args:
            days: Number of days to look back

        Returns:
            List of HistoryEntry objects, newest first
        """
        cutoff = datetime.now() - timedelta(days=days)
        return [e for e in self._entries if e.timestamp > cutoff]

    def delete_old(self, days: int) -> int:
        """Delete entries older than specified days.

        Args:
            days: Delete entries older than this

        Returns:
            Number of deleted entries
        """
        cutoff = datetime.now() - timedelta(days=days)
        old_count = len(self._entries)
        self._entries = [e for e in self._entries if e.timestamp > cutoff]
        deleted = old_count - len(self._entries)
        if deleted > 0:
            self._save()
        return deleted

    def clear(self) -> None:
        """Delete all history entries."""
        self._entries = []
        self._save()

    def get_by_id(self, entry_id: int) -> Optional[HistoryEntry]:
        """Get single entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            HistoryEntry or None if not found
        """
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)
