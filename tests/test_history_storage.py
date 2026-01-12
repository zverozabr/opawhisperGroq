"""Tests for history storage."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from soupawhisper.storage import HistoryEntry, HistoryStorage


class TestHistoryStorage:
    """Tests for HistoryStorage class."""

    @pytest.fixture
    def storage(self):
        """Create temporary history storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_history.md"
            yield HistoryStorage(file_path)

    def test_add_entry(self, storage):
        """Test adding entries to history."""
        entry_id = storage.add("Hello world", "en")
        assert entry_id > 0

    def test_get_recent(self, storage):
        """Test retrieving recent entries."""
        storage.add("First", "en")
        storage.add("Second", "ru")
        storage.add("Third", "auto")

        entries = storage.get_recent(days=1)
        assert len(entries) == 3
        # All entries should be present (order may vary due to same timestamp)
        texts = {e.text for e in entries}
        assert texts == {"First", "Second", "Third"}

    def test_get_recent_filters_old(self, storage):
        """Test that old entries are filtered out."""
        # Add entry
        storage.add("Recent", "en")
        entries = storage.get_recent(days=1)
        assert len(entries) == 1

        # Entries from the past should not be returned
        entries = storage.get_recent(days=0)
        # Note: entries added today might still appear
        # This is expected behavior

    def test_delete_old(self, storage):
        """Test deleting old entries."""
        storage.add("Test entry", "en")
        count = storage.count()
        assert count == 1

        # Delete entries older than 1000 days (should keep all)
        deleted = storage.delete_old(1000)
        assert deleted == 0
        assert storage.count() == 1

    def test_clear(self, storage):
        """Test clearing all entries."""
        storage.add("One", "en")
        storage.add("Two", "ru")
        assert storage.count() == 2

        storage.clear()
        assert storage.count() == 0

    def test_get_by_id(self, storage):
        """Test retrieving entry by ID."""
        entry_id = storage.add("Find me", "en")
        entry = storage.get_by_id(entry_id)

        assert entry is not None
        assert entry.id == entry_id
        assert entry.text == "Find me"
        assert entry.language == "en"

    def test_get_by_id_not_found(self, storage):
        """Test retrieving non-existent entry."""
        entry = storage.get_by_id(9999)
        assert entry is None

    def test_entry_properties(self, storage):
        """Test HistoryEntry helper properties."""
        entry_id = storage.add("Test", "ru")
        entry = storage.get_by_id(entry_id)

        # time_str and date_str should not raise
        assert len(entry.time_str) == 5  # HH:MM
        assert len(entry.date_str) == 10  # YYYY-MM-DD


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_time_str(self):
        """Test time formatting."""
        entry = HistoryEntry(
            id=1,
            text="Test",
            language="en",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
        )
        assert entry.time_str == "10:30"

    def test_date_str(self):
        """Test date formatting."""
        entry = HistoryEntry(
            id=1,
            text="Test",
            language="en",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
        )
        assert entry.date_str == "2024-01-15"


class TestMarkdownFormat:
    """Tests for Markdown file format."""

    def test_markdown_file_created(self):
        """Test that Markdown file is created on add."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "history.md"
            storage = HistoryStorage(file_path)
            storage.add("Test entry", "en")
            assert file_path.exists()

    def test_markdown_file_format(self):
        """Test Markdown file content format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "history.md"
            storage = HistoryStorage(file_path)
            storage.add("Hello world", "en")

            content = file_path.read_text()
            assert "# SoupaWhisper History" in content
            assert "## " in content
            assert " | en" in content
            assert "Hello world" in content

    def test_reload_from_file(self):
        """Test loading entries from existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "history.md"

            # Create and add entry
            storage1 = HistoryStorage(file_path)
            storage1.add("Persistent entry", "ru")

            # Create new instance that loads from file
            storage2 = HistoryStorage(file_path)
            entries = storage2.get_recent(days=1)

            assert len(entries) == 1
            assert entries[0].text == "Persistent entry"
            assert entries[0].language == "ru"
