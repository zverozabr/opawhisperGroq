"""Pytest configuration for the test suite."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure Playwright to use system Chrome installation."""
    return {
        **browser_type_launch_args,
        "channel": "chrome",  # Use system Google Chrome
    }


# =============================================================================
# Shared TUI Test Fixtures (DRY)
# =============================================================================


@pytest.fixture
def mock_config():
    """Create mock config with all required fields.

    DRY: Single source of truth for mock config in all TUI tests.
    """
    config = MagicMock()
    config.hotkey = "ctrl_r"
    config.history_days = 3
    config.history_enabled = True
    config.debug = False
    config.api_key = "test_key_12345"
    config.active_provider = "groq"
    config.model = "whisper-large-v3"
    config.language = "auto"
    config.auto_type = True
    config.auto_enter = False
    config.typing_delay = 12
    config.notifications = True
    config.backend = "auto"
    config.audio_device = "default"
    return config


@pytest.fixture
def mock_history_entries():
    """Create mock history entries for testing."""
    from datetime import datetime

    return [
        {
            "id": "1",
            "text": "Hello world, this is a test transcription",
            "language": "en",
            "timestamp": datetime.now(),
        },
        {
            "id": "2",
            "text": "Привет мир, это тестовая транскрипция",
            "language": "ru",
            "timestamp": datetime.now(),
        },
    ]


@pytest.fixture
def tui_app_patched(mock_config):
    """Create patched TUIApp for testing.

    DRY: Single source of truth for TUI app fixture.
    Patches Config.load, HistoryStorage, and WorkerController.
    """
    with patch("soupawhisper.tui.app.Config.load", return_value=mock_config):
        with patch("soupawhisper.tui.app.HistoryStorage") as mock_history:
            with patch("soupawhisper.tui.app.WorkerController"):
                mock_history.return_value.get_recent.return_value = []
                from soupawhisper.tui.app import TUIApp

                app = TUIApp(test_mode=True)
                yield app


@pytest.fixture
def tui_app_with_history(mock_config, mock_history_entries):
    """Create TUIApp with mock history data for E2E tests."""
    with patch("soupawhisper.tui.app.Config.load", return_value=mock_config):
        with patch("soupawhisper.tui.app.HistoryStorage") as mock_storage:
            with patch("soupawhisper.tui.app.WorkerController"):
                mock_storage.return_value.get_recent.return_value = mock_history_entries
                from soupawhisper.tui.app import TUIApp

                app = TUIApp(test_mode=True)
                yield app
