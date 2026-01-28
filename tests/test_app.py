"""Unit tests for App class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.app import App, validate_config
from soupawhisper.config import Config


@pytest.fixture
def mock_config():
    """Create mock configuration with API key."""
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
    )


@pytest.fixture
def mock_backend():
    """Create mock display backend."""
    backend = MagicMock()
    backend.stop = MagicMock()
    backend.listen_hotkey = MagicMock()
    backend.type_text = MagicMock()
    backend.copy_to_clipboard = MagicMock()
    return backend


@pytest.fixture
def mock_recorder():
    """Create mock audio recorder."""
    recorder = MagicMock()
    recorder.is_recording = False
    recorder.start = MagicMock()
    recorder.stop = MagicMock(return_value=Path("/tmp/test.wav"))
    recorder.cleanup = MagicMock()
    return recorder


class TestAppInitialization:
    """Test App initialization."""

    def test_init_with_config(self, mock_config, mock_backend):
        """Test App initializes with config."""
        with patch("soupawhisper.app.AudioRecorder") as MockRecorder:
            MockRecorder.return_value = MagicMock()

            app = App(config=mock_config, backend=mock_backend)

            assert app.config == mock_config
            assert app.backend == mock_backend
            MockRecorder.assert_called_once_with(device="default")

    def test_validate_config_requires_api_key_for_cloud(self):
        """validate_config reports missing API key for cloud provider."""
        config = Config(api_key="", active_provider="groq")
        errors = validate_config(config)
        assert errors
        assert "API key" in errors[0]

    def test_validate_config_allows_local_without_api_key(self):
        """validate_config allows local providers without API key."""
        config = Config(api_key="", active_provider="local-mlx")
        errors = validate_config(config)
        assert errors == []

    def test_init_creates_backend_if_none(self, mock_config):
        """Test App creates backend if none provided."""
        with patch("soupawhisper.app.AudioRecorder"):
            with patch("soupawhisper.app.create_backend") as mock_create:
                mock_create.return_value = MagicMock()

                app = App(config=mock_config, backend=None)

                mock_create.assert_called_once_with(mock_config.backend, mock_config.typing_delay)
                assert app.backend is not None

    def test_init_with_callbacks(self, mock_config, mock_backend):
        """Test App stores callbacks."""
        on_transcription = MagicMock()
        on_recording = MagicMock()
        on_transcribing = MagicMock()

        with patch("soupawhisper.app.AudioRecorder"):
            app = App(
                config=mock_config,
                backend=mock_backend,
                on_transcription=on_transcription,
                on_recording=on_recording,
                on_transcribing=on_transcribing,
            )

            assert app.on_transcription == on_transcription
            assert app.on_recording == on_recording
            assert app.on_transcribing == on_transcribing

    def test_init_creates_debug_storage_when_debug(self, mock_backend):
        """Test debug storage created when debug=True."""
        config = Config(api_key="test_key", debug=True)

        with patch("soupawhisper.app.AudioRecorder"):
            with patch("soupawhisper.app.DebugStorage") as MockDebug:
                MockDebug.return_value = MagicMock()

                app = App(config=config, backend=mock_backend)

                MockDebug.assert_called_once()
                assert app._debug_storage is not None


class TestAppRecording:
    """Test recording functionality."""

    def test_on_press_starts_recording(self, mock_config, mock_backend, mock_recorder):
        """Test _on_press starts recording."""
        on_recording = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            app = App(config=mock_config, backend=mock_backend, on_recording=on_recording)

            app._on_press()

            mock_recorder.start.assert_called_once()
            on_recording.assert_called_once_with(True)

    def test_on_press_skips_if_already_recording(self, mock_config, mock_backend, mock_recorder):
        """Test _on_press is ignored if already recording."""
        mock_recorder.is_recording = True
        on_recording = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            app = App(config=mock_config, backend=mock_backend, on_recording=on_recording)

            app._on_press()

            mock_recorder.start.assert_not_called()
            on_recording.assert_not_called()

    def test_on_release_stops_recording(self, mock_config, mock_backend, mock_recorder):
        """Test _on_release stops recording."""
        mock_recorder.is_recording = True
        on_recording = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch.object(App, "_transcribe_async"):
                app = App(config=mock_config, backend=mock_backend, on_recording=on_recording)

                app._on_release()

                mock_recorder.stop.assert_called_once()
                on_recording.assert_called_once_with(False)

    def test_on_release_skips_if_not_recording(self, mock_config, mock_backend, mock_recorder):
        """Test _on_release is ignored if not recording."""
        mock_recorder.is_recording = False
        on_recording = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            app = App(config=mock_config, backend=mock_backend, on_recording=on_recording)

            app._on_release()

            mock_recorder.stop.assert_not_called()
            on_recording.assert_not_called()

    def test_on_release_skips_transcription_if_no_audio(self, mock_config, mock_backend, mock_recorder):
        """Test _on_release skips transcription if recorder returns None."""
        mock_recorder.is_recording = True
        mock_recorder.stop.return_value = None

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("threading.Thread") as MockThread:
                app = App(config=mock_config, backend=mock_backend)

                app._on_release()

                MockThread.assert_not_called()


class TestAppTranscription:
    """Test transcription functionality."""

    def test_transcribe_async_calls_handler(self, mock_config, mock_backend, mock_recorder):
        """Test _transcribe_async delegates to handler."""
        on_transcribing = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.TranscriptionHandler") as MockHandler:
                mock_handler = MagicMock()
                MockHandler.return_value = mock_handler

                app = App(config=mock_config, backend=mock_backend, on_transcribing=on_transcribing)

                app._transcribe_async("/tmp/test.wav")

                mock_handler.handle.assert_called_once()
                mock_recorder.cleanup.assert_called_once()

    def test_transcribe_async_notifies_state(self, mock_config, mock_backend, mock_recorder):
        """Test _transcribe_async notifies transcribing state."""
        on_transcribing = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.TranscriptionHandler") as MockHandler:
                mock_handler = MagicMock()
                MockHandler.return_value = mock_handler

                app = App(config=mock_config, backend=mock_backend, on_transcribing=on_transcribing)

                app._transcribe_async("/tmp/test.wav")

                # Should be called with True then False
                assert on_transcribing.call_count == 2
                on_transcribing.assert_any_call(True)
                on_transcribing.assert_any_call(False)

    def test_transcribe_async_prevents_concurrent(self, mock_config, mock_backend, mock_recorder):
        """Test _transcribe_async prevents concurrent transcription."""
        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.TranscriptionHandler") as MockHandler:
                mock_handler = MagicMock()
                MockHandler.return_value = mock_handler

                app = App(config=mock_config, backend=mock_backend)
                app._transcribing = True  # Simulate ongoing transcription

                app._transcribe_async("/tmp/test.wav")

                mock_handler.handle.assert_not_called()

    def test_transcribe_async_cleans_up_on_error(self, mock_config, mock_backend, mock_recorder):
        """Test _transcribe_async cleans up even on error."""
        on_transcribing = MagicMock()

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.TranscriptionHandler") as MockHandler:
                mock_handler = MagicMock()
                mock_handler.handle.side_effect = Exception("Test error")
                MockHandler.return_value = mock_handler

                app = App(config=mock_config, backend=mock_backend, on_transcribing=on_transcribing)

                with pytest.raises(Exception):
                    app._transcribe_async("/tmp/test.wav")

                # Cleanup should still be called
                mock_recorder.cleanup.assert_called_once()
                # State should be reset
                assert app._transcribing is False


class TestAppLifecycle:
    """Test App lifecycle methods."""

    def test_stop_calls_backend_stop(self, mock_config, mock_backend, mock_recorder):
        """Test stop() calls backend.stop()."""
        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            app = App(config=mock_config, backend=mock_backend)

            app.stop()

            mock_backend.stop.assert_called_once()

    def test_run_calls_listen_hotkey(self, mock_config, mock_backend, mock_recorder):
        """Test run() starts hotkey listening."""
        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            app = App(config=mock_config, backend=mock_backend)

            app.run()

            mock_backend.listen_hotkey.assert_called_once_with(
                mock_config.hotkey,
                app._on_press,
                app._on_release,
            )


class TestAppNotifications:
    """Test notification functionality."""

    def test_notify_when_enabled(self, mock_backend, mock_recorder):
        """Test notifications work when enabled."""
        config = Config(api_key="test_key", notifications=True)

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.notify") as mock_notify:
                app = App(config=config, backend=mock_backend)

                app._notify("Test", "Message")

                mock_notify.assert_called_once()

    def test_notify_when_disabled(self, mock_backend, mock_recorder):
        """Test notifications skipped when disabled."""
        config = Config(api_key="test_key", notifications=False)

        with patch("soupawhisper.app.AudioRecorder", return_value=mock_recorder):
            with patch("soupawhisper.app.notify") as mock_notify:
                app = App(config=config, backend=mock_backend)

                app._notify("Test", "Message")

                mock_notify.assert_not_called()
