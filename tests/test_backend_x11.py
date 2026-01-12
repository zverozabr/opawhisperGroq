"""Tests for X11 backend."""

import sys
from unittest.mock import MagicMock, patch

import pytest


# Mock pynput before importing X11Backend
@pytest.fixture(autouse=True)
def mock_pynput():
    """Mock pynput module for testing without X server."""
    mock_keyboard = MagicMock()
    mock_keyboard.Key = MagicMock()
    mock_keyboard.KeyCode = MagicMock()
    mock_keyboard.Listener = MagicMock()
    mock_keyboard.Controller = MagicMock()

    with patch.dict(sys.modules, {'pynput': MagicMock(), 'pynput.keyboard': mock_keyboard}):
        yield mock_keyboard


class TestX11Backend:
    """Tests for X11Backend."""

    def test_copy_to_clipboard(self, mock_pynput):
        """Test clipboard copy calls shared clipboard module."""
        with patch("soupawhisper.backend.x11._copy") as mock_copy:
            # Import after mocking
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            backend.copy_to_clipboard("тест")

            mock_copy.assert_called_once_with("тест")

    def test_type_text(self, mock_pynput):
        """Test text typing uses xdotool type."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            method = backend.type_text("привет")

            mock_run.assert_called_once_with(
                ["xdotool", "type", "--delay", "12", "--clearmodifiers", "--", "привет"],
                check=False,
            )
            assert method == "xdotool"

    def test_press_key_enter(self, mock_pynput):
        """Test pressing Enter key."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            backend.press_key("enter")

            mock_run.assert_called_once_with(
                ["xdotool", "key", "--clearmodifiers", "Return"],
                check=False,
            )

    def test_press_key_tab(self, mock_pynput):
        """Test pressing Tab key."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            backend.press_key("tab")

            mock_run.assert_called_once_with(
                ["xdotool", "key", "--clearmodifiers", "Tab"],
                check=False,
            )

    def test_type_text_returns_method(self, mock_pynput):
        """Test type_text returns method name."""
        with patch("subprocess.run"):
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            method = backend.type_text("test")
            assert method == "xdotool"
