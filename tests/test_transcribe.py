"""Tests for transcription via OpenAICompatibleProvider.

Note: This file tests the legacy transcribe() function for backward compatibility
and the modern OpenAICompatibleProvider.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.providers import (
    OpenAICompatibleProvider,
    ProviderConfig,
    TranscriptionError,
    TranscriptionResult,
)


class TestOpenAICompatibleProviderTranscription:
    """Tests for OpenAICompatibleProvider transcription."""

    @pytest.fixture
    def provider(self):
        """Create a test provider."""
        config = ProviderConfig(
            name="test-groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key="test-key",
            model="whisper-large-v3",
        )
        return OpenAICompatibleProvider(config)

    def test_transcribe_with_language(self, provider):
        """Test transcription with explicit language."""
        with patch("soupawhisper.providers.openai_compatible.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "привет мир"}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = provider.transcribe(audio_path, "ru")

            assert isinstance(result, TranscriptionResult)
            assert result.text == "привет мир"
            assert result.raw_response == {"text": "привет мир"}
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["data"]["language"] == "ru"
            assert call_kwargs["data"]["model"] == "whisper-large-v3"

    def test_transcribe_auto_language(self, provider):
        """Test transcription with auto language detection."""
        with patch("soupawhisper.providers.openai_compatible.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "hello world"}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = provider.transcribe(audio_path, "auto")

            assert isinstance(result, TranscriptionResult)
            assert result.text == "hello world"
            call_kwargs = mock_post.call_args[1]
            assert "language" not in call_kwargs["data"]

    def test_transcribe_api_error(self, provider):
        """Test API error handling."""
        with patch("soupawhisper.providers.openai_compatible.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            with pytest.raises(TranscriptionError, match="API error 401"):
                provider.transcribe(audio_path, "ru")

    def test_transcribe_empty_result(self, provider):
        """Test handling of empty transcription result."""
        with patch("soupawhisper.providers.openai_compatible.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = {"text": "  "}
            mock_post.return_value = mock_response

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"fake audio data")
                audio_path = f.name

            result = provider.transcribe(audio_path, "ru")
            assert isinstance(result, TranscriptionResult)
            assert result.text == ""

    def test_provider_name(self, provider):
        """Test provider name property."""
        assert provider.name == "test-groq"

    def test_is_available_with_key(self, provider):
        """Test is_available returns True with API key."""
        assert provider.is_available() is True

    def test_is_available_without_key(self):
        """Test is_available returns False without API key."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=None,
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.is_available() is False

    def test_is_available_without_url(self):
        """Test is_available returns False without URL."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url=None,
            api_key="test-key",
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.is_available() is False
