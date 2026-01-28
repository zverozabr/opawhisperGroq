"""E2E tests for real audio transcription.

These tests use actual audio files and the Groq API to verify
the full transcription pipeline works correctly.

Requirements:
- GROQ_API_KEY environment variable or config file with API key
- Test audio fixtures in tests/fixtures/
"""

import os
from pathlib import Path

import pytest

from soupawhisper.config import Config, CONFIG_PATH
from soupawhisper.transcribe import transcribe


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def get_api_key() -> str | None:
    """Get Groq API key from environment or config."""
    # Try environment first
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key

    # Fall back to config file
    try:
        config = Config.load(CONFIG_PATH)
        if config.api_key and config.api_key != "your_groq_api_key_here":
            return config.api_key
    except Exception:
        pass

    return None


@pytest.fixture
def api_key():
    """Get API key or skip test."""
    key = get_api_key()
    if not key:
        pytest.skip("Groq API key not available")
    return key


@pytest.fixture
def russian_speech_audio():
    """Path to Russian speech test audio."""
    path = FIXTURES_DIR / "test_russian_speech.wav"
    if not path.exists():
        pytest.skip(f"Test audio not found: {path}")
    return path


class TestRealAudioTranscription:
    """E2E tests using real audio files and Groq API."""

    def test_transcribe_russian_speech(self, api_key, russian_speech_audio):
        """Test transcription of Russian speech audio.

        Audio content: "раз два раз два три 4 5 выше зайчик погулять"
        """
        result = transcribe(
            audio_path=str(russian_speech_audio),
            api_key=api_key,
            model="whisper-large-v3",
            language="auto",
        )

        # Should have non-empty transcription
        assert result.text, "Transcription should not be empty"

        # Should be more than just noise ("you")
        assert len(result.text) > 5, "Transcription should be substantial"
        assert result.text.lower().strip() != "you", "Should not be just noise"

        # Should contain Russian text (numbers or words)
        russian_indicators = ["раз", "два", "три", "зайчик", "1", "2", "3", "4", "5"]
        has_russian = any(indicator in result.text.lower() for indicator in russian_indicators)
        assert has_russian, f"Should contain Russian content, got: {result.text}"

    def test_transcribe_with_explicit_russian_language(self, api_key, russian_speech_audio):
        """Test transcription with explicit Russian language hint."""
        result = transcribe(
            audio_path=str(russian_speech_audio),
            api_key=api_key,
            model="whisper-large-v3",
            language="ru",
        )

        assert result.text, "Transcription should not be empty"
        # With explicit language hint, should definitely contain Russian
        assert any(c in result.text for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"), \
            f"With ru language, should contain Cyrillic, got: {result.text}"


class TestAudioRecorderWithRealDevice:
    """Tests for AudioRecorder with real microphone.

    These tests require a working microphone and are skipped in CI.
    """

    @pytest.mark.skip(reason="Requires real microphone - run manually")
    def test_record_and_transcribe_live(self, api_key):
        """Record from microphone and transcribe.

        Run this test manually with:
            pytest tests/test_real_audio_e2e.py::TestAudioRecorderWithRealDevice -v --no-header -rN
        """
        import time
        from soupawhisper.audio import AudioRecorder

        # Use BY-V microphone (device 1) - adjust for your system
        recorder = AudioRecorder(device="1")

        print("\nRecording for 3 seconds... Speak something!")
        recorder.start()
        time.sleep(3)
        audio_path = recorder.stop()

        assert audio_path is not None, "Should have recorded file"
        assert audio_path.exists(), "Audio file should exist"
        assert audio_path.stat().st_size > 1000, "Audio file should have content"

        # Transcribe
        result = transcribe(
            audio_path=str(audio_path),
            api_key=api_key,
            model="whisper-large-v3",
            language="auto",
        )

        print(f"Transcription: {result.text}")

        # Cleanup
        recorder.cleanup()

        # Basic validation
        assert result.text, "Should have transcription"


class TestTranscriptionEdgeCases:
    """Test edge cases in transcription."""

    def test_transcription_result_structure(self, api_key, russian_speech_audio):
        """Test that transcription result has expected structure."""
        result = transcribe(
            audio_path=str(russian_speech_audio),
            api_key=api_key,
            model="whisper-large-v3",
            language="auto",
        )

        # Check result structure
        assert hasattr(result, "text"), "Result should have text attribute"
        assert hasattr(result, "raw_response"), "Result should have raw_response"
        assert isinstance(result.text, str), "Text should be string"
        assert isinstance(result.raw_response, dict), "Raw response should be dict"

    def test_transcription_is_stripped(self, api_key, russian_speech_audio):
        """Test that transcription text is properly stripped."""
        result = transcribe(
            audio_path=str(russian_speech_audio),
            api_key=api_key,
            model="whisper-large-v3",
            language="auto",
        )

        # Text should not have leading/trailing whitespace
        assert result.text == result.text.strip(), "Text should be stripped"
