"""Tests for debug storage."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from soupawhisper.storage.debug import DebugData, DebugRecord, DebugStorage, MAX_RECORDINGS


class TestDebugStorage:
    """Tests for DebugStorage class."""

    @pytest.fixture
    def storage(self):
        """Create temporary debug storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DebugStorage(Path(tmpdir) / "debug")

    @pytest.fixture
    def audio_file(self):
        """Create temporary audio file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio data for testing")
            yield Path(f.name)
        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def sample_debug_data(self):
        """Create sample debug data."""
        return DebugData(
            text="hello world",
            clipboard_text="hello world",
            typed_text="hello world",
            typing_method="xdotool",
        )

    @pytest.fixture
    def sample_response(self):
        """Create sample API response."""
        return {"text": "hello world", "model": "whisper-large-v3"}

    def test_save_creates_files(self, storage, audio_file, sample_debug_data, sample_response):
        """Test that save() creates all required files."""
        record_dir = storage.save(audio_file, sample_debug_data, sample_response)

        assert (record_dir / "audio.wav").exists()
        assert (record_dir / "text.txt").exists()
        assert (record_dir / "clipboard.txt").exists()
        assert (record_dir / "typed.txt").exists()
        assert (record_dir / "response.json").exists()

        # Verify content
        assert (record_dir / "text.txt").read_text() == "hello world"
        assert (record_dir / "clipboard.txt").read_text() == "hello world"
        assert "Method: xdotool" in (record_dir / "typed.txt").read_text()
        assert json.loads((record_dir / "response.json").read_text()) == sample_response

    def test_rotation_keeps_max_recordings(self, storage, audio_file, sample_debug_data, sample_response):
        """Test that only MAX_RECORDINGS are kept."""
        # Create more than MAX_RECORDINGS
        for i in range(MAX_RECORDINGS + 2):
            storage.save(audio_file, sample_debug_data, sample_response)
            time.sleep(0.001)  # Small delay for unique timestamps

        recordings = storage.list_recordings()
        assert len(recordings) == MAX_RECORDINGS

    def test_list_recordings_order(self, storage, audio_file, sample_response):
        """Test recordings are returned newest first."""
        data1 = DebugData(
            text="first",
            clipboard_text="first",
            typed_text="first",
            typing_method="xdotool",
        )
        data2 = DebugData(
            text="second",
            clipboard_text="second",
            typed_text="second",
            typing_method="wtype",
        )

        storage.save(audio_file, data1, sample_response)
        time.sleep(0.01)  # Ensure different timestamp
        storage.save(audio_file, data2, sample_response)

        recordings = storage.list_recordings()
        assert recordings[0].text == "second"
        assert recordings[1].text == "first"

    def test_clear(self, storage, audio_file, sample_debug_data, sample_response):
        """Test clearing all recordings."""
        storage.save(audio_file, sample_debug_data, sample_response)

        storage.clear()

        assert len(storage.list_recordings()) == 0

    def test_typing_method_parsed(self, storage, audio_file, sample_response):
        """Test that typing method is correctly parsed from typed.txt."""
        data = DebugData(
            text="test",
            clipboard_text="test",
            typed_text="test",
            typing_method="wtype",
        )

        storage.save(audio_file, data, sample_response)

        recordings = storage.list_recordings()
        assert len(recordings) == 1
        assert recordings[0].typing_method == "wtype"


class TestDebugData:
    """Tests for DebugData dataclass."""

    def test_debug_data_fields(self):
        """Test DebugData stores all fields."""
        data = DebugData(
            text="recognized",
            clipboard_text="clipboard",
            typed_text="typed",
            typing_method="xdotool",
        )

        assert data.text == "recognized"
        assert data.clipboard_text == "clipboard"
        assert data.typed_text == "typed"
        assert data.typing_method == "xdotool"


class TestDebugRecord:
    """Tests for DebugRecord dataclass."""

    def test_debug_record_fields(self):
        """Test DebugRecord stores all fields."""
        record = DebugRecord(
            timestamp="20240101_120000",
            audio_path=Path("/tmp/audio.wav"),
            text="recognized",
            clipboard_text="clipboard",
            typed_text="typed",
            typing_method="xdotool",
            response={"text": "recognized"},
        )

        assert record.timestamp == "20240101_120000"
        assert record.audio_path == Path("/tmp/audio.wav")
        assert record.text == "recognized"
        assert record.typing_method == "xdotool"
