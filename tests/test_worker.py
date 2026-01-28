"""Tests for WorkerManager.

TDD: Tests for framework-agnostic worker management.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from soupawhisper.config import Config
from soupawhisper.worker import WorkerManager


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return Config(api_key="test_api_key_12345")


class TestWorkerManagerInit:
    """Test WorkerManager initialization."""

    def test_init_with_config(self, mock_config):
        """WorkerManager initializes with config."""
        worker = WorkerManager(mock_config)

        assert worker.config == mock_config
        assert worker.core is None
        assert not worker.is_running

    def test_init_with_callbacks(self, mock_config):
        """WorkerManager accepts optional callbacks."""
        on_recording = MagicMock()
        on_transcription = MagicMock()
        on_transcribing = MagicMock()
        on_error = MagicMock()

        worker = WorkerManager(
            mock_config,
            on_recording=on_recording,
            on_transcription=on_transcription,
            on_transcribing=on_transcribing,
            on_error=on_error,
        )

        assert worker._on_recording == on_recording
        assert worker._on_transcription == on_transcription
        assert worker._on_transcribing == on_transcribing
        assert worker._on_error == on_error


class TestWorkerManagerStart:
    """Test WorkerManager start/stop."""

    @patch("soupawhisper.backend.create_backend")
    @patch("soupawhisper.app.App")
    def test_start_creates_thread(self, mock_app_class, mock_create_backend, mock_config):
        """start() creates a daemon thread."""
        worker = WorkerManager(mock_config)

        # Mock App to not actually run
        mock_app = MagicMock()
        mock_app.run = MagicMock()
        mock_app_class.return_value = mock_app

        worker.start()

        # Give thread time to start
        time.sleep(0.1)

        assert worker.is_running or worker._thread is not None

        # Cleanup
        worker.stop()

    @patch("soupawhisper.backend.create_backend")
    @patch("soupawhisper.app.App")
    def test_start_with_runner(self, mock_app_class, mock_create_backend, mock_config):
        """start_with_runner() uses provided thread runner."""
        worker = WorkerManager(mock_config)

        mock_runner = MagicMock()
        worker.start_with_runner(mock_runner)

        assert worker.is_running
        mock_runner.assert_called_once()

        # Cleanup
        worker.stop()

    def test_start_twice_warns(self, mock_config):
        """Starting twice logs warning."""
        worker = WorkerManager(mock_config)
        worker._running = True  # Simulate already running

        with patch("soupawhisper.worker.log") as mock_log:
            worker.start()
            mock_log.warning.assert_called_once()


class TestWorkerManagerStop:
    """Test WorkerManager stop."""

    def test_stop_sets_running_false(self, mock_config):
        """stop() sets running to False."""
        worker = WorkerManager(mock_config)
        worker._running = True

        worker.stop()

        assert not worker.is_running

    @patch("soupawhisper.backend.create_backend")
    @patch("soupawhisper.app.App")
    def test_stop_calls_core_stop(self, mock_app_class, mock_create_backend, mock_config):
        """stop() calls core.stop() if core exists."""
        worker = WorkerManager(mock_config)

        mock_core = MagicMock()
        worker._core = mock_core
        worker._running = True

        worker.stop()

        mock_core.stop.assert_called_once()
        assert worker._core is None


class TestWorkerManagerCallbacks:
    """Test WorkerManager callback handling."""

    @patch("soupawhisper.backend.create_backend")
    @patch("soupawhisper.app.App")
    def test_callbacks_passed_to_app(self, mock_app_class, mock_create_backend, mock_config):
        """Callbacks are passed to App instance."""
        on_recording = MagicMock()
        on_transcription = MagicMock()
        on_transcribing = MagicMock()

        worker = WorkerManager(
            mock_config,
            on_recording=on_recording,
            on_transcription=on_transcription,
            on_transcribing=on_transcribing,
        )

        # Manually call worker loop to test App creation
        mock_app = MagicMock()
        mock_app.run = MagicMock()
        mock_app_class.return_value = mock_app

        worker._worker_loop()

        # Verify App was created with callbacks
        mock_app_class.assert_called_once()
        call_kwargs = mock_app_class.call_args.kwargs
        assert call_kwargs["on_recording"] == on_recording
        assert call_kwargs["on_transcription"] == on_transcription
        assert call_kwargs["on_transcribing"] == on_transcribing

    @patch("soupawhisper.backend.create_backend")
    @patch("soupawhisper.app.App")
    def test_error_callback_on_exception(self, mock_app_class, mock_create_backend, mock_config):
        """on_error callback called when exception occurs."""
        on_error = MagicMock()

        worker = WorkerManager(mock_config, on_error=on_error)

        # Make App.run raise exception
        mock_app = MagicMock()
        mock_app.run.side_effect = Exception("Test error")
        mock_app_class.return_value = mock_app

        worker._worker_loop()

        on_error.assert_called_once_with("Test error")


class TestUIEventsProtocol:
    """Test ui_events.py protocols."""

    def test_recording_handler_protocol(self):
        """RecordingHandler protocol is runtime checkable."""
        from soupawhisper.ui_events import RecordingHandler

        class MyHandler:
            def on_recording_changed(self, is_recording: bool) -> None:
                pass

        handler = MyHandler()
        assert isinstance(handler, RecordingHandler)

    def test_transcription_handler_protocol(self):
        """TranscriptionHandler protocol is runtime checkable."""
        from soupawhisper.ui_events import TranscriptionHandler

        class MyHandler:
            def on_transcription_complete(self, text: str, language: str) -> None:
                pass

            def on_transcribing_changed(self, is_transcribing: bool) -> None:
                pass

        handler = MyHandler()
        assert isinstance(handler, TranscriptionHandler)

    def test_ui_event_handler_protocol(self):
        """UIEventHandler combined protocol is runtime checkable."""
        from soupawhisper.ui_events import UIEventHandler

        class MyHandler:
            def on_recording_changed(self, is_recording: bool) -> None:
                pass

            def on_transcription_complete(self, text: str, language: str) -> None:
                pass

            def on_transcribing_changed(self, is_transcribing: bool) -> None:
                pass

            def on_error(self, message: str) -> None:
                pass

        handler = MyHandler()
        assert isinstance(handler, UIEventHandler)
