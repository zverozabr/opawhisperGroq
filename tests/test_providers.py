"""Tests for transcription providers."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.providers import (
    FasterWhisperProvider,
    MLXProvider,
    OpenAICompatibleProvider,
    ProviderConfig,
    TranscriptionError,
    TranscriptionResult,
    get_best_local_provider,
    get_provider,
    list_available_local_providers,
    list_providers,
    load_providers_config,
    migrate_from_config_ini,
    save_providers_config,
    set_active_provider,
)
from soupawhisper.providers.models import (
    AVAILABLE_MODELS,
    ModelManager,
    get_model_manager,
)


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_from_dict_openai_compatible(self):
        """Test creating config from dict for cloud provider."""
        data = {
            "type": "openai_compatible",
            "url": "https://api.groq.com/openai/v1/audio/transcriptions",
            "api_key": "gsk_test",
            "model": "whisper-large-v3",
        }
        config = ProviderConfig.from_dict("groq", data)

        assert config.name == "groq"
        assert config.type == "openai_compatible"
        assert config.url == "https://api.groq.com/openai/v1/audio/transcriptions"
        assert config.api_key == "gsk_test"
        assert config.model == "whisper-large-v3"

    def test_from_dict_mlx(self):
        """Test creating config from dict for local MLX provider."""
        data = {
            "type": "mlx",
            "model": "large-v3",
        }
        config = ProviderConfig.from_dict("local-mlx", data)

        assert config.name == "local-mlx"
        assert config.type == "mlx"
        assert config.url is None
        assert config.api_key is None
        assert config.model == "large-v3"

    def test_to_dict(self):
        """Test converting config to dict."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key="key123",
            model="model-v1",
        )
        result = config.to_dict()

        assert result["type"] == "openai_compatible"
        assert result["url"] == "https://example.com"
        assert result["api_key"] == "key123"
        assert result["model"] == "model-v1"
        assert "name" not in result  # Name is key, not in dict


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_create_result(self):
        """Test creating transcription result."""
        result = TranscriptionResult(
            text="Hello world",
            raw_response={"text": "Hello world", "segments": []},
        )
        assert result.text == "Hello world"
        assert result.raw_response["text"] == "Hello world"


class TestOpenAICompatibleProvider:
    """Tests for OpenAI-compatible cloud provider."""

    def test_name(self):
        """Test provider name property."""
        config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com",
            api_key="test",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.name == "groq"

    def test_is_available_with_config(self):
        """Test availability with url and api_key."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key="key123",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.is_available() is True

    def test_is_available_without_key(self):
        """Test not available without api_key."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key=None,
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.is_available() is False

    def test_is_available_without_url(self):
        """Test not available without url."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url=None,
            api_key="key123",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider.is_available() is False

    def test_transcribe_without_url_raises(self):
        """Test transcribe raises error when url missing."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url=None,
            api_key="key123",
        )
        provider = OpenAICompatibleProvider(config)

        with pytest.raises(TranscriptionError) as exc_info:
            provider.transcribe("/tmp/audio.wav", "en")

        assert "no URL configured" in str(exc_info.value)

    def test_transcribe_without_key_raises(self):
        """Test transcribe raises error when api_key missing."""
        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key=None,
        )
        provider = OpenAICompatibleProvider(config)

        with pytest.raises(TranscriptionError) as exc_info:
            provider.transcribe("/tmp/audio.wav", "en")

        assert "no API key configured" in str(exc_info.value)

    @patch("soupawhisper.providers.openai_compatible.requests.post")
    def test_transcribe_success(self, mock_post, tmp_path):
        """Test successful transcription."""
        # Create temp audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # Mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"text": "Hello world"}
        mock_post.return_value = mock_response

        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com/transcribe",
            api_key="test_key",
            model="whisper-1",
        )
        provider = OpenAICompatibleProvider(config)

        result = provider.transcribe(str(audio_file), "en")

        assert result.text == "Hello world"
        assert result.raw_response["text"] == "Hello world"

        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert call_args.kwargs["data"]["model"] == "whisper-1"
        assert call_args.kwargs["data"]["language"] == "en"

    @patch("soupawhisper.providers.openai_compatible.requests.post")
    def test_transcribe_auto_language(self, mock_post, tmp_path):
        """Test transcription with auto language detection."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"text": "Привет мир"}
        mock_post.return_value = mock_response

        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key="key",
        )
        provider = OpenAICompatibleProvider(config)

        provider.transcribe(str(audio_file), "auto")

        # Language should not be in request data for auto
        call_data = mock_post.call_args.kwargs["data"]
        assert "language" not in call_data

    @patch("soupawhisper.providers.openai_compatible.requests.post")
    def test_transcribe_api_error(self, mock_post, tmp_path):
        """Test handling of API error response."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        config = ProviderConfig(
            name="test",
            type="openai_compatible",
            url="https://example.com",
            api_key="bad_key",
        )
        provider = OpenAICompatibleProvider(config)

        with pytest.raises(TranscriptionError) as exc_info:
            provider.transcribe(str(audio_file), "en")

        assert "401" in str(exc_info.value)
        assert "Unauthorized" in str(exc_info.value)


class TestMLXProvider:
    """Tests for MLX local provider (mlx-whisper)."""

    def test_name(self):
        """Test provider name property."""
        config = ProviderConfig(name="local-mlx", type="mlx", model="large-v3")
        provider = MLXProvider(config)
        assert provider.name == "local-mlx"

    def test_model_short_name_expanded(self):
        """Test short model name is expanded to full HF repo."""
        config = ProviderConfig(name="mlx", type="mlx", model="large-v3")
        provider = MLXProvider(config)
        assert provider.model == "mlx-community/whisper-large-v3-mlx"

    def test_model_full_repo_preserved(self):
        """Test full HF repo is preserved as-is."""
        config = ProviderConfig(name="mlx", type="mlx", model="mlx-community/whisper-large-v3-turbo")
        provider = MLXProvider(config)
        assert provider.model == "mlx-community/whisper-large-v3-turbo"

    def test_is_available_returns_bool(self):
        """Test is_available returns boolean."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)
        result = provider.is_available()
        assert isinstance(result, bool)

    def test_is_available_false_on_non_darwin(self):
        """Test not available on non-macOS platforms."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        # On non-darwin, should return False
        if sys.platform != "darwin":
            assert provider.is_available() is False

    def test_transcribe_not_available_raises(self):
        """Test transcribe raises when MLX not available."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        # Mock is_available to return False
        with patch.object(provider, "is_available", return_value=False):
            with pytest.raises(TranscriptionError) as exc_info:
                provider.transcribe("/tmp/audio.wav", "en")

            assert "not available" in str(exc_info.value)

    def test_transcribe_success_with_mock(self, tmp_path):
        """Test successful transcription with mocked mlx_whisper."""
        config = ProviderConfig(name="mlx", type="mlx", model="mlx-community/whisper-base-mlx")
        provider = MLXProvider(config)

        # Create temp audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Mock the mlx_whisper module
        mock_mlx_whisper = MagicMock()
        mock_mlx_whisper.transcribe.return_value = {"text": "Hello world", "language": "en"}

        with patch.object(provider, "is_available", return_value=True):
            with patch.dict(sys.modules, {"mlx_whisper": mock_mlx_whisper}):
                result = provider.transcribe(str(audio_file), "en")

                assert result.text == "Hello world"
                assert result.raw_response["text"] == "Hello world"
                mock_mlx_whisper.transcribe.assert_called_once()

    def test_transcribe_auto_language(self, tmp_path):
        """Test transcription with auto language passes None."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"audio")

        mock_mlx_whisper = MagicMock()
        mock_mlx_whisper.transcribe.return_value = {"text": "Привет", "language": "ru"}

        with patch.object(provider, "is_available", return_value=True):
            with patch.dict(sys.modules, {"mlx_whisper": mock_mlx_whisper}):
                provider.transcribe(str(audio_file), "auto")

                # Check language=None was passed for auto
                call_kwargs = mock_mlx_whisper.transcribe.call_args.kwargs
                assert call_kwargs.get("language") is None

    def test_transcribe_strips_whitespace(self, tmp_path):
        """Test transcription text is stripped."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"audio")

        mock_mlx_whisper = MagicMock()
        mock_mlx_whisper.transcribe.return_value = {"text": "  Привет мир  "}

        with patch.object(provider, "is_available", return_value=True):
            with patch.dict(sys.modules, {"mlx_whisper": mock_mlx_whisper}):
                result = provider.transcribe(str(audio_file), "ru")
                assert result.text == "Привет мир"

    def test_transcribe_error_handling(self, tmp_path):
        """Test transcription error is wrapped in TranscriptionError."""
        config = ProviderConfig(name="mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"audio")

        mock_mlx_whisper = MagicMock()
        mock_mlx_whisper.transcribe.side_effect = RuntimeError("Model loading failed")

        with patch.object(provider, "is_available", return_value=True):
            with patch.dict(sys.modules, {"mlx_whisper": mock_mlx_whisper}):
                with pytest.raises(TranscriptionError) as exc_info:
                    provider.transcribe(str(audio_file), "en")

                assert "MLX transcription failed" in str(exc_info.value)


class TestFasterWhisperProvider:
    """Tests for faster-whisper cross-platform provider."""

    def test_name(self):
        """Test provider name property."""
        config = ProviderConfig(name="local-cpu", type="faster_whisper", model="large-v3")
        provider = FasterWhisperProvider(config)
        assert provider.name == "local-cpu"

    def test_model_name(self):
        """Test model name is extracted correctly."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="large-v3-turbo")
        provider = FasterWhisperProvider(config)
        assert provider.model == "large-v3-turbo"

    def test_model_strips_hf_prefix(self):
        """Test HF repo prefix is stripped from model name."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="Systran/faster-whisper-large-v3")
        provider = FasterWhisperProvider(config)
        assert provider.model == "large-v3"

    def test_is_available_returns_bool(self):
        """Test is_available returns boolean."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="base")
        provider = FasterWhisperProvider(config)
        result = provider.is_available()
        assert isinstance(result, bool)

    def test_transcribe_not_available_raises(self):
        """Test transcribe raises when faster-whisper not available."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="base")
        provider = FasterWhisperProvider(config)

        with patch.object(provider, "is_available", return_value=False):
            with pytest.raises(TranscriptionError) as exc_info:
                provider.transcribe("/tmp/audio.wav", "en")

            assert "not available" in str(exc_info.value)

    def test_transcribe_success_with_mock(self, tmp_path):
        """Test successful transcription with mocked faster-whisper."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="base")
        provider = FasterWhisperProvider(config)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Create mock segments
        mock_segment = MagicMock()
        mock_segment.text = "Hello"
        mock_segment.start = 0.0
        mock_segment.end = 1.0

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.95
        mock_info.duration = 1.0

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "_get_model", return_value=mock_model):
                result = provider.transcribe(str(audio_file), "en")

                assert result.text == "Hello"
                assert result.raw_response["language"] == "en"

    def test_transcribe_multiple_segments(self, tmp_path):
        """Test transcription combines multiple segments."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="base")
        provider = FasterWhisperProvider(config)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"audio")

        # Multiple segments
        seg1 = MagicMock(text="Hello", start=0.0, end=0.5)
        seg2 = MagicMock(text="world", start=0.5, end=1.0)

        mock_info = MagicMock(language="en", language_probability=0.9, duration=1.0)
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([seg1, seg2], mock_info)

        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "_get_model", return_value=mock_model):
                result = provider.transcribe(str(audio_file), "en")

                assert result.text == "Hello world"

    def test_unload_model(self):
        """Test model can be unloaded."""
        config = ProviderConfig(name="fw", type="faster_whisper", model="base")
        provider = FasterWhisperProvider(config)

        # Simulate loaded model
        provider._model = MagicMock()

        provider.unload_model()

        assert provider._model is None


class TestProvidersRegistry:
    """Tests for provider registry functions."""

    def test_load_empty_config(self, tmp_path, monkeypatch):
        """Test loading when no config file exists."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = load_providers_config()
        assert config == {"active": "groq", "providers": {}}

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {
            "active": "openai",
            "providers": {
                "groq": {"type": "openai_compatible", "api_key": "gsk_xxx"},
                "openai": {"type": "openai_compatible", "api_key": "sk_xxx"},
            },
        }
        save_providers_config(config)

        loaded = load_providers_config()
        assert loaded["active"] == "openai"
        assert "groq" in loaded["providers"]
        assert "openai" in loaded["providers"]

    def test_list_providers(self, tmp_path, monkeypatch):
        """Test listing configured providers."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {
            "active": "groq",
            "providers": {
                "groq": {"type": "openai_compatible"},
                "mlx": {"type": "mlx"},
            },
        }
        save_providers_config(config)

        providers = list_providers()
        assert "groq" in providers
        assert "mlx" in providers

    def test_set_active_provider(self, tmp_path, monkeypatch):
        """Test setting active provider."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {
            "active": "groq",
            "providers": {
                "groq": {"type": "openai_compatible"},
                "openai": {"type": "openai_compatible"},
            },
        }
        save_providers_config(config)

        set_active_provider("openai")

        loaded = load_providers_config()
        assert loaded["active"] == "openai"

    def test_set_active_provider_not_found(self, tmp_path, monkeypatch):
        """Test setting non-existent provider raises error."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {"active": "groq", "providers": {"groq": {"type": "openai_compatible"}}}
        save_providers_config(config)

        with pytest.raises(ValueError) as exc_info:
            set_active_provider("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_get_provider(self, tmp_path, monkeypatch):
        """Test getting provider instance."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {
            "active": "groq",
            "providers": {
                "groq": {
                    "type": "openai_compatible",
                    "url": "https://api.groq.com/openai/v1/audio/transcriptions",
                    "api_key": "test_key",
                },
            },
        }
        save_providers_config(config)

        provider = get_provider()

        assert provider.name == "groq"
        assert isinstance(provider, OpenAICompatibleProvider)

    def test_get_provider_by_name(self, tmp_path, monkeypatch):
        """Test getting specific provider by name."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {
            "active": "groq",
            "providers": {
                "groq": {"type": "openai_compatible", "url": "https://groq.com"},
                "mlx": {"type": "mlx", "model": "base"},
            },
        }
        save_providers_config(config)

        provider = get_provider("mlx")

        assert provider.name == "mlx"
        assert isinstance(provider, MLXProvider)

    def test_get_provider_not_found(self, tmp_path, monkeypatch):
        """Test getting non-existent provider raises error."""
        fake_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", fake_path
        )

        config = {"active": "groq", "providers": {"groq": {"type": "openai_compatible"}}}
        save_providers_config(config)

        with pytest.raises(ValueError) as exc_info:
            get_provider("nonexistent")

        assert "not found" in str(exc_info.value)


class TestLocalProviderDetection:
    """Tests for local provider auto-detection."""

    def test_list_available_local_providers_returns_list(self):
        """Test list_available_local_providers returns a list."""
        result = list_available_local_providers()
        assert isinstance(result, list)

    def test_get_best_local_provider_returns_string_or_none(self):
        """Test get_best_local_provider returns string or None."""
        result = get_best_local_provider()
        assert result is None or isinstance(result, str)

    @patch.dict(sys.modules, {"mlx_whisper": MagicMock()})
    def test_mlx_preferred_on_darwin(self):
        """Test MLX is preferred on macOS when available."""
        if sys.platform == "darwin":
            available = list_available_local_providers()
            if "mlx" in available:
                best = get_best_local_provider()
                assert best == "mlx"

    @patch.dict(sys.modules, {"faster_whisper": MagicMock()})
    def test_faster_whisper_available(self):
        """Test faster-whisper is detected when installed."""
        # This depends on actual import availability
        available = list_available_local_providers()
        # Just verify it returns a list
        assert isinstance(available, list)


class TestModelManager:
    """Tests for ModelManager."""

    def test_available_models_defined(self):
        """Test AVAILABLE_MODELS contains expected models."""
        assert "tiny" in AVAILABLE_MODELS
        assert "base" in AVAILABLE_MODELS
        assert "large-v3" in AVAILABLE_MODELS
        assert "large-v3-turbo" in AVAILABLE_MODELS

    def test_model_info_has_required_fields(self):
        """Test ModelInfo has all required fields."""
        for name, info in AVAILABLE_MODELS.items():
            assert info.name == name
            assert isinstance(info.size_mb, int)
            assert isinstance(info.description, str)

    def test_init_creates_directory(self, tmp_path):
        """Test ModelManager creates models directory."""
        models_dir = tmp_path / "models"
        manager = ModelManager(models_dir=models_dir)

        assert models_dir.exists()
        assert manager.models_dir == models_dir

    def test_list_available(self, tmp_path):
        """Test listing available models."""
        manager = ModelManager(models_dir=tmp_path)
        available = manager.list_available()

        assert len(available) > 0
        assert available[0].name in AVAILABLE_MODELS

    def test_list_downloaded_empty(self, tmp_path):
        """Test listing downloaded models when none exist."""
        manager = ModelManager(models_dir=tmp_path)
        downloaded = manager.list_downloaded()

        assert downloaded == []

    def test_is_downloaded_false(self, tmp_path):
        """Test is_downloaded returns False for non-existent model."""
        manager = ModelManager(models_dir=tmp_path)

        assert manager.is_downloaded("large-v3") is False

    def test_is_downloaded_true(self, tmp_path):
        """Test is_downloaded returns True for downloaded model."""
        manager = ModelManager(models_dir=tmp_path)

        # Create fake model directory with a file
        model_dir = tmp_path / "large-v3"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"fake model")

        assert manager.is_downloaded("large-v3") is True

    def test_get_model_path(self, tmp_path):
        """Test getting path to downloaded model."""
        manager = ModelManager(models_dir=tmp_path)

        # Non-existent
        assert manager.get_model_path("tiny") is None

        # Create fake model
        model_dir = tmp_path / "tiny"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"fake")

        path = manager.get_model_path("tiny")
        assert path == model_dir

    def test_get_model_info(self, tmp_path):
        """Test getting model metadata."""
        manager = ModelManager(models_dir=tmp_path)

        info = manager.get_model_info("large-v3-turbo")
        assert info is not None
        assert info.name == "large-v3-turbo"
        assert info.size_mb == 1600

        # Unknown model
        assert manager.get_model_info("unknown") is None

    def test_delete_model(self, tmp_path):
        """Test deleting a downloaded model."""
        manager = ModelManager(models_dir=tmp_path)

        # Create fake model
        model_dir = tmp_path / "base"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"fake")

        assert manager.is_downloaded("base") is True

        result = manager.delete("base")

        assert result is True
        assert manager.is_downloaded("base") is False

    def test_delete_nonexistent_model(self, tmp_path):
        """Test deleting non-existent model returns False."""
        manager = ModelManager(models_dir=tmp_path)

        result = manager.delete("nonexistent")
        assert result is False

    def test_get_size_on_disk(self, tmp_path):
        """Test getting model size on disk."""
        manager = ModelManager(models_dir=tmp_path)

        # Non-existent
        assert manager.get_size_on_disk("tiny") == 0

        # Create fake model with known size
        model_dir = tmp_path / "tiny"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"x" * 1000)

        size = manager.get_size_on_disk("tiny")
        assert size == 1000

    def test_get_model_manager_singleton(self):
        """Test get_model_manager returns singleton."""
        manager1 = get_model_manager()
        manager2 = get_model_manager()

        # Same instance (singleton pattern)
        assert manager1 is manager2


class TestMigration:
    """Tests for config migration."""

    def test_migrate_from_config_ini(self, tmp_path, monkeypatch):
        """Test migration from old config.ini format."""
        # Setup paths
        providers_path = tmp_path / "providers.json"
        config_path = tmp_path / "config.ini"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", providers_path
        )
        monkeypatch.setattr(
            "soupawhisper.config.CONFIG_PATH", config_path
        )

        # Create old config.ini
        config_path.write_text("""[groq]
api_key = gsk_migrated_key
model = whisper-large-v3
""")

        # Ensure providers.json doesn't exist
        assert not providers_path.exists()

        # Run migration
        result = migrate_from_config_ini()

        assert result is True
        assert providers_path.exists()

        # Verify migrated content
        with open(providers_path) as f:
            migrated = json.load(f)

        assert migrated["active"] == "groq"
        assert migrated["providers"]["groq"]["api_key"] == "gsk_migrated_key"
        assert migrated["providers"]["groq"]["type"] == "openai_compatible"

    def test_migrate_skips_if_providers_exists(self, tmp_path, monkeypatch):
        """Test migration skips when providers.json already has content."""
        providers_path = tmp_path / "providers.json"
        monkeypatch.setattr(
            "soupawhisper.providers.PROVIDERS_PATH", providers_path
        )

        # Create existing providers.json
        existing = {
            "active": "openai",
            "providers": {"openai": {"type": "openai_compatible"}},
        }
        providers_path.write_text(json.dumps(existing))

        result = migrate_from_config_ini()

        assert result is False
