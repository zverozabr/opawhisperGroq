"""Unit tests for TranscriptionHandler class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.config import Config
from soupawhisper.providers import TranscriptionError, TranscriptionResult
from soupawhisper.transcription_handler import TranscriptionContext, TranscriptionHandler


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return Config(
        api_key="test_api_key",
        model="whisper-large-v3",
        language="auto",
        hotkey="ctrl_r",
        auto_type=True,
        auto_enter=False,
        typing_delay=12,
        notifications=False,
        backend="auto",
        audio_device="default",
        active_provider="groq",
    )


@pytest.fixture
def mock_backend():
    """Create mock display backend."""
    backend = MagicMock()
    backend.copy_to_clipboard = MagicMock()
    backend.type_text = MagicMock(return_value="keyboard")
    backend.press_key = MagicMock()
    return backend


@pytest.fixture
def mock_debug_storage():
    """Create mock debug storage."""
    storage = MagicMock()
    storage.save = MagicMock()
    return storage


@pytest.fixture
def mock_provider():
    """Create mock transcription provider."""
    provider = MagicMock()
    provider.transcribe = MagicMock(
        return_value=TranscriptionResult(
            text="test transcription",
            raw_response={"text": "test transcription"},
        )
    )
    return provider


class TestTranscriptionHandlerInit:
    """Test TranscriptionHandler initialization."""

    def test_init_stores_notification_setting(self, mock_config):
        """Test handler stores notification setting."""
        handler = TranscriptionHandler(mock_config)
        assert handler._notifications_enabled is False

        mock_config.notifications = True
        handler = TranscriptionHandler(mock_config)
        assert handler._notifications_enabled is True


class TestTranscriptionHandlerHandle:
    """Test TranscriptionHandler.handle() method."""

    def test_handle_successful_transcription(self, mock_config, mock_backend, mock_provider):
        """Test successful transcription flow."""
        on_complete = MagicMock()

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
                on_complete=on_complete,
            )

            result = handler.handle(ctx)

            assert result == "test transcription"
            mock_provider.transcribe.assert_called_once_with("/tmp/test.wav", "auto")
            mock_backend.copy_to_clipboard.assert_called_once_with("test transcription")
            on_complete.assert_called_once_with("test transcription", "auto")

    def test_handle_empty_transcription(self, mock_config, mock_backend):
        """Test handling empty transcription result."""
        mock_provider = MagicMock()
        mock_provider.transcribe.return_value = TranscriptionResult(
            text="",
            raw_response={"text": ""},
        )
        on_complete = MagicMock()

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
                on_complete=on_complete,
            )

            result = handler.handle(ctx)

            assert result is None
            mock_backend.copy_to_clipboard.assert_not_called()
            on_complete.assert_not_called()

    def test_handle_transcription_error(self, mock_config, mock_backend):
        """Test handling transcription API error."""
        mock_provider = MagicMock()
        mock_provider.transcribe.side_effect = TranscriptionError("API error 401")
        on_complete = MagicMock()

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
                on_complete=on_complete,
            )

            result = handler.handle(ctx)

            assert result is None
            mock_backend.copy_to_clipboard.assert_not_called()
            on_complete.assert_not_called()


class TestTranscriptionHandlerProcessResult:
    """Test _process_result method."""

    def test_copies_to_clipboard(self, mock_config, mock_backend, mock_provider):
        """Test result is copied to clipboard."""
        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            handler.handle(ctx)

            mock_backend.copy_to_clipboard.assert_called_once_with("test transcription")

    def test_types_text_when_auto_type_enabled(self, mock_config, mock_backend, mock_provider):
        """Test text is typed when auto_type is enabled."""
        mock_config.auto_type = True

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            handler.handle(ctx)

            mock_backend.type_text.assert_called_once_with("test transcription")

    def test_skips_typing_when_auto_type_disabled(self, mock_config, mock_backend, mock_provider):
        """Test text is not typed when auto_type is disabled."""
        mock_config.auto_type = False

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            handler.handle(ctx)

            mock_backend.type_text.assert_not_called()

    def test_presses_enter_when_auto_enter_enabled(self, mock_config, mock_backend, mock_provider):
        """Test Enter is pressed when auto_enter is enabled."""
        mock_config.auto_type = True
        mock_config.auto_enter = True

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            handler.handle(ctx)

            mock_backend.press_key.assert_called_once_with("enter")

    def test_skips_enter_when_auto_enter_disabled(self, mock_config, mock_backend, mock_provider):
        """Test Enter is not pressed when auto_enter is disabled."""
        mock_config.auto_type = True
        mock_config.auto_enter = False

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            handler.handle(ctx)

            mock_backend.press_key.assert_not_called()

    def test_saves_debug_data_when_storage_provided(
        self, mock_config, mock_backend, mock_debug_storage, mock_provider
    ):
        """Test debug data is saved when storage is provided."""
        mock_config.auto_type = True

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=mock_debug_storage,
            )

            handler.handle(ctx)

            mock_debug_storage.save.assert_called_once()
            call_args = mock_debug_storage.save.call_args
            assert call_args[0][0] == Path("/tmp/test.wav")  # audio_path

    def test_skips_debug_data_when_no_storage(self, mock_config, mock_backend, mock_provider):
        """Test debug data is not saved when no storage provided."""
        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            handler = TranscriptionHandler(mock_config)
            ctx = TranscriptionContext(
                audio_path=Path("/tmp/test.wav"),
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
            )

            # Should not raise
            handler.handle(ctx)


class TestTranscriptionHandlerNotifications:
    """Test notification functionality."""

    def test_notify_when_enabled(self):
        """Test notifications are sent when enabled."""
        config = Config(api_key="test", notifications=True)

        with patch("soupawhisper.transcription_handler.notify") as mock_notify:
            handler = TranscriptionHandler(config)
            handler._notify("Test", "Message")

            mock_notify.assert_called_once()

    def test_notify_when_disabled(self):
        """Test notifications are skipped when disabled."""
        config = Config(api_key="test", notifications=False)

        with patch("soupawhisper.transcription_handler.notify") as mock_notify:
            handler = TranscriptionHandler(config)
            handler._notify("Test", "Message")

            mock_notify.assert_not_called()

    def test_error_notification_on_api_failure(self, mock_config, mock_backend):
        """Test error notification is shown on API failure."""
        mock_config.notifications = True
        mock_provider = MagicMock()
        mock_provider.transcribe.side_effect = TranscriptionError("API error 500")

        with patch("soupawhisper.transcription_handler.get_provider", return_value=mock_provider):
            with patch("soupawhisper.transcription_handler.notify") as mock_notify:
                handler = TranscriptionHandler(mock_config)
                ctx = TranscriptionContext(
                    audio_path=Path("/tmp/test.wav"),
                    config=mock_config,
                    backend=mock_backend,
                    debug_storage=None,
                )

                handler.handle(ctx)

                mock_notify.assert_called_once()
                assert "Error" in mock_notify.call_args[0][0]


class TestTranscriptionContext:
    """Test TranscriptionContext dataclass."""

    def test_context_creation(self, mock_config, mock_backend):
        """Test context can be created with all fields."""
        on_complete = MagicMock()

        ctx = TranscriptionContext(
            audio_path=Path("/tmp/test.wav"),
            config=mock_config,
            backend=mock_backend,
            debug_storage=None,
            on_complete=on_complete,
        )

        assert ctx.audio_path == Path("/tmp/test.wav")
        assert ctx.config == mock_config
        assert ctx.backend == mock_backend
        assert ctx.debug_storage is None
        assert ctx.on_complete == on_complete

    def test_context_default_on_complete(self, mock_config, mock_backend):
        """Test context defaults on_complete to None."""
        ctx = TranscriptionContext(
            audio_path=Path("/tmp/test.wav"),
            config=mock_config,
            backend=mock_backend,
            debug_storage=None,
        )

        assert ctx.on_complete is None
