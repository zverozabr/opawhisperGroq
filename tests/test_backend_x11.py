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
        """Test clipboard copy uses xclip."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            # Import after mocking
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            backend.copy_to_clipboard("тест")

            mock_popen.assert_called_once()
            assert mock_popen.call_args[0][0] == ["xclip", "-selection", "clipboard"]
            mock_process.communicate.assert_called_once_with(input="тест".encode())

    def test_type_text(self, mock_pynput):
        """Test text typing uses xdotool."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend()
            backend.type_text("привет")

            mock_run.assert_called_once_with(
                ["xdotool", "type", "--delay", "12", "--clearmodifiers", "привет"],
                check=False,
            )

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

    def test_type_text_custom_delay(self, mock_pynput):
        """Test text typing with custom delay."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.x11 import X11Backend
            backend = X11Backend(typing_delay=0)
            backend.type_text("fast")

            mock_run.assert_called_once_with(
                ["xdotool", "type", "--delay", "0", "--clearmodifiers", "fast"],
                check=False,
            )
