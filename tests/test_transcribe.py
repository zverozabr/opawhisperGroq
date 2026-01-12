"""Tests for transcription."""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.transcribe import TranscriptionError, TranscriptionResult, transcribe


class TestTranscribe:
    """Tests for transcribe function."""

    def test_transcribe_with_language(self):
        """Test transcription with explicit language."""
        with patch("soupawhisper.transcribe.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "привет мир"}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = transcribe(audio_path, "test-key", "whisper-large-v3", "ru")

            assert isinstance(result, TranscriptionResult)
            assert result.text == "привет мир"
            assert result.raw_response == {"text": "привет мир"}
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["data"]["language"] == "ru"
            assert call_kwargs["data"]["model"] == "whisper-large-v3"

    def test_transcribe_auto_language(self):
        """Test transcription with auto language detection."""
        with patch("soupawhisper.transcribe.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "hello world"}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = transcribe(audio_path, "test-key", "whisper-large-v3", "auto")

            assert isinstance(result, TranscriptionResult)
            assert result.text == "hello world"
            call_kwargs = mock_post.call_args[1]
            assert "language" not in call_kwargs["data"]

    def test_transcribe_api_error(self):
        """Test API error handling."""
        with patch("soupawhisper.transcribe.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            with pytest.raises(TranscriptionError, match="API error 401"):
                transcribe(audio_path, "invalid-key", "whisper-large-v3", "ru")

    def test_transcribe_empty_result(self):
        """Test handling of empty transcription result."""
        with patch("soupawhisper.transcribe.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "  "}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = transcribe(audio_path, "test-key", "whisper-large-v3", "ru")
            assert isinstance(result, TranscriptionResult)
            assert result.text == ""
