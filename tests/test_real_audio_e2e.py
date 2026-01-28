"""E2E tests for real audio transcription.

These tests use actual audio files and transcription providers to verify
the full transcription pipeline works correctly.

Requirements:
- For cloud tests: GROQ_API_KEY environment variable or config file with API key
- For local tests: mlx-whisper (macOS) or faster-whisper installed
- Test audio fixtures in tests/fixtures/
"""

import os
import sys
from pathlib import Path

import pytest

from soupawhisper.config import CONFIG_PATH, Config
from soupawhisper.providers import (
    FasterWhisperProvider,
    MLXProvider,
    OpenAICompatibleProvider,
    ProviderConfig,
    get_provider,
    list_available_local_providers,
    load_providers_config,
)
from soupawhisper.providers.models import AVAILABLE_MODELS

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def get_api_key() -> str | None:
    """Get Groq API key from environment or config."""
    # Try environment first
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key

    # Fall back to providers.json
    try:
        config = load_providers_config()
        groq_config = config.get("providers", {}).get("groq", {})
        key = groq_config.get("api_key", "")
        if key and key != "your_groq_api_key_here":
            return key
    except Exception:
        pass

    # Fall back to old config.ini
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


class TestGroqProviderE2E:
    """E2E tests using Groq cloud API."""

    def test_transcribe_russian_speech(self, api_key, russian_speech_audio):
        """Test transcription of Russian speech audio via Groq.

        Audio content: "раз два раз два три 4 5 выше зайчик погулять"
        """
        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=api_key,
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)

        result = provider.transcribe(str(russian_speech_audio), "auto")

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
        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=api_key,
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)

        result = provider.transcribe(str(russian_speech_audio), "ru")

        assert result.text, "Transcription should not be empty"
        # With explicit language hint, should definitely contain Russian
        assert any(c in result.text for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"), \
            f"With ru language, should contain Cyrillic, got: {result.text}"

    def test_result_structure(self, api_key, russian_speech_audio):
        """Test that transcription result has expected structure."""
        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=api_key,
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)

        result = provider.transcribe(str(russian_speech_audio), "auto")

        # Check result structure
        assert hasattr(result, "text"), "Result should have text attribute"
        assert hasattr(result, "raw_response"), "Result should have raw_response"
        assert isinstance(result.text, str), "Text should be string"
        assert isinstance(result.raw_response, dict), "Raw response should be dict"

        # Text should be stripped
        assert result.text == result.text.strip(), "Text should be stripped"


@pytest.mark.skipif(sys.platform != "darwin", reason="MLX only available on macOS")
class TestMLXProviderE2E:
    """E2E tests using local MLX provider (macOS only)."""

    @pytest.fixture
    def mlx_available(self):
        """Check if MLX is available, skip if not."""
        if "mlx" not in list_available_local_providers():
            pytest.skip("mlx-whisper not installed")

    def test_transcribe_with_tiny_model(self, mlx_available, russian_speech_audio):
        """Test transcription with tiny model (fastest, for testing)."""
        config = ProviderConfig(
            name="local-mlx",
            type="mlx",
            model="mlx-community/whisper-tiny-mlx",
        )
        provider = MLXProvider(config)

        if not provider.is_available():
            pytest.skip("MLX provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        # Should have some transcription (tiny model may not be accurate)
        assert result.text, "Transcription should not be empty"
        assert isinstance(result.text, str)

    def test_transcribe_with_base_model(self, mlx_available, russian_speech_audio):
        """Test transcription with base model (better accuracy)."""
        config = ProviderConfig(
            name="local-mlx",
            type="mlx",
            model="mlx-community/whisper-base-mlx",
        )
        provider = MLXProvider(config)

        if not provider.is_available():
            pytest.skip("MLX provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        assert result.text, "Transcription should not be empty"
        # Base model should produce reasonable output
        assert len(result.text) > 3, "Should have meaningful transcription"

    def test_transcribe_with_language_hint(self, mlx_available, russian_speech_audio):
        """Test transcription with Russian language hint."""
        config = ProviderConfig(
            name="local-mlx",
            type="mlx",
            model="mlx-community/whisper-tiny-mlx",
        )
        provider = MLXProvider(config)

        if not provider.is_available():
            pytest.skip("MLX provider not available")

        result = provider.transcribe(str(russian_speech_audio), "ru")

        assert result.text, "Transcription should not be empty"
        # With Russian hint, should produce Cyrillic
        assert any(c in result.text for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"), \
            f"With ru language, should contain Cyrillic, got: {result.text}"

    def test_result_structure(self, mlx_available, russian_speech_audio):
        """Test MLX result has expected structure."""
        config = ProviderConfig(
            name="local-mlx",
            type="mlx",
            model="mlx-community/whisper-tiny-mlx",
        )
        provider = MLXProvider(config)

        if not provider.is_available():
            pytest.skip("MLX provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        assert hasattr(result, "text")
        assert hasattr(result, "raw_response")
        assert isinstance(result.raw_response, dict)
        # MLX returns segments and language
        assert "text" in result.raw_response or result.text


class TestFasterWhisperProviderE2E:
    """E2E tests using faster-whisper provider (cross-platform)."""

    @pytest.fixture
    def faster_whisper_available(self):
        """Check if faster-whisper is available, skip if not."""
        if "faster_whisper" not in list_available_local_providers():
            pytest.skip("faster-whisper not installed")

    def test_transcribe_with_tiny_model(self, faster_whisper_available, russian_speech_audio):
        """Test transcription with tiny model (fastest, for testing)."""
        config = ProviderConfig(
            name="local-fw",
            type="faster_whisper",
            model="tiny",
        )
        provider = FasterWhisperProvider(config)

        if not provider.is_available():
            pytest.skip("faster-whisper provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        # Should have some transcription
        assert result.text, "Transcription should not be empty"
        assert isinstance(result.text, str)

    def test_transcribe_with_base_model(self, faster_whisper_available, russian_speech_audio):
        """Test transcription with base model (better accuracy)."""
        config = ProviderConfig(
            name="local-fw",
            type="faster_whisper",
            model="base",
        )
        provider = FasterWhisperProvider(config)

        if not provider.is_available():
            pytest.skip("faster-whisper provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        assert result.text, "Transcription should not be empty"
        assert len(result.text) > 3, "Should have meaningful transcription"

    def test_transcribe_with_language_hint(self, faster_whisper_available, russian_speech_audio):
        """Test transcription with Russian language hint.

        Note: Uses 'base' model because 'tiny' is too small to reliably
        produce Cyrillic output even with explicit language hint.
        """
        config = ProviderConfig(
            name="local-fw",
            type="faster_whisper",
            model="base",  # Use base model - tiny is unreliable for Cyrillic
        )
        provider = FasterWhisperProvider(config)

        if not provider.is_available():
            pytest.skip("faster-whisper provider not available")

        result = provider.transcribe(str(russian_speech_audio), "ru")

        assert result.text, "Transcription should not be empty"
        # With Russian hint and base model, should produce Cyrillic
        assert any(c in result.text for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"), \
            f"With ru language, should contain Cyrillic, got: {result.text}"

    def test_result_has_segments(self, faster_whisper_available, russian_speech_audio):
        """Test faster-whisper result includes segments."""
        config = ProviderConfig(
            name="local-fw",
            type="faster_whisper",
            model="tiny",
        )
        provider = FasterWhisperProvider(config)

        if not provider.is_available():
            pytest.skip("faster-whisper provider not available")

        result = provider.transcribe(str(russian_speech_audio), "auto")

        # faster-whisper should return segments and duration
        assert "segments" in result.raw_response
        assert "duration" in result.raw_response
        assert "language" in result.raw_response


class TestProviderRegistryE2E:
    """E2E tests for provider registry integration."""

    def test_get_provider_by_name(self, api_key, russian_speech_audio, tmp_path, monkeypatch):
        """Test getting and using provider from registry."""
        # Setup temporary providers.json
        providers_path = tmp_path / "providers.json"
        monkeypatch.setattr("soupawhisper.providers.PROVIDERS_PATH", providers_path)

        import json
        providers_config = {
            "active": "groq",
            "providers": {
                "groq": {
                    "type": "openai_compatible",
                    "url": "https://api.groq.com/openai/v1/audio/transcriptions",
                    "api_key": api_key,
                    "model": "whisper-large-v3",
                },
            },
        }
        providers_path.write_text(json.dumps(providers_config))

        # Get provider from registry
        provider = get_provider("groq")

        assert provider.name == "groq"
        assert isinstance(provider, OpenAICompatibleProvider)

        # Use it for transcription
        result = provider.transcribe(str(russian_speech_audio), "auto")
        assert result.text


class TestModelManager:
    """E2E tests for model manager (no actual downloads in CI)."""

    def test_model_manager_lists_models(self, tmp_path):
        """Test model manager can list available models."""
        from soupawhisper.providers.models import ModelManager

        manager = ModelManager(models_dir=tmp_path)

        available = manager.list_available()

        assert len(available) >= 6  # At least 6 models defined
        names = [m.name for m in available]
        assert "tiny" in names
        assert "large-v3" in names

    def test_model_info_correct(self):
        """Test model info is correct."""
        assert "large-v3-turbo" in AVAILABLE_MODELS

        info = AVAILABLE_MODELS["large-v3-turbo"]
        assert info.size_mb == 1600
        assert info.mlx_repo is not None
        assert info.faster_whisper_name is not None


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

        # Use default microphone
        recorder = AudioRecorder(device="default")

        print("\nRecording for 3 seconds... Speak something!")
        recorder.start()
        time.sleep(3)
        audio_path = recorder.stop()

        assert audio_path is not None, "Should have recorded file"
        assert audio_path.exists(), "Audio file should exist"
        assert audio_path.stat().st_size > 1000, "Audio file should have content"

        # Transcribe with Groq
        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=api_key,
            model="whisper-large-v3",
        )
        provider = OpenAICompatibleProvider(config)
        result = provider.transcribe(str(audio_path), "auto")

        print(f"Transcription: {result.text}")

        # Cleanup
        recorder.cleanup()

        # Basic validation
        assert result.text, "Should have transcription"
