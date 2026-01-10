"""Tests for macOS (Darwin) backend."""

import sys
from unittest.mock import MagicMock, patch

import pytest


# Mock pynput before importing DarwinBackend
@pytest.fixture(autouse=True)
def mock_pynput():
    """Mock pynput module for testing without macOS."""
    mock_keyboard = MagicMock()
    mock_keyboard.Key = MagicMock()
    mock_keyboard.Key.enter = "enter"
    mock_keyboard.Key.tab = "tab"
    mock_keyboard.Key.esc = "esc"
    mock_keyboard.Key.space = "space"
    mock_keyboard.Key.backspace = "backspace"
    mock_keyboard.Key.cmd = "cmd"
    mock_keyboard.Key.cmd_r = "cmd_r"
    mock_keyboard.KeyCode = MagicMock()
    mock_keyboard.Listener = MagicMock()
    mock_keyboard.Controller = MagicMock()

    with patch.dict(sys.modules, {'pynput': MagicMock(), 'pynput.keyboard': mock_keyboard}):
        yield mock_keyboard


class TestDarwinBackend:
    """Tests for DarwinBackend."""

    def test_copy_to_clipboard(self, mock_pynput):
        """Test clipboard copy uses pbcopy."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            from soupawhisper.backend.darwin import DarwinBackend
            backend = DarwinBackend()
            backend.copy_to_clipboard("тест")

            mock_popen.assert_called_once()
            assert mock_popen.call_args[0][0] == ["pbcopy"]
            mock_process.communicate.assert_called_once_with(input="тест".encode())

    def test_type_text(self, mock_pynput):
        """Test text typing uses pynput controller."""
        mock_controller = MagicMock()

        with patch("soupawhisper.backend.darwin.keyboard.Controller", return_value=mock_controller):
            from soupawhisper.backend.darwin import DarwinBackend
            backend = DarwinBackend()
            backend.type_text("hello")

            mock_controller.type.assert_called_once_with("hello")

    def test_press_key_enter(self, mock_pynput):
        """Test pressing Enter key."""
        mock_controller = MagicMock()

        with patch("soupawhisper.backend.darwin.keyboard.Controller", return_value=mock_controller):
            from soupawhisper.backend.darwin import DarwinBackend
            backend = DarwinBackend()
            backend.press_key("enter")

            # Should press and release the key
            assert mock_controller.press.called
            assert mock_controller.release.called

    def test_press_key_tab(self, mock_pynput):
        """Test pressing Tab key."""
        mock_controller = MagicMock()

        with patch("soupawhisper.backend.darwin.keyboard.Controller", return_value=mock_controller):
            from soupawhisper.backend.darwin import DarwinBackend
            backend = DarwinBackend()
            backend.press_key("tab")

            assert mock_controller.press.called
            assert mock_controller.release.called


class TestDarwinDetection:
    """Tests for macOS platform detection."""

    def test_detect_darwin(self):
        """Test macOS detection."""
        with patch.object(sys, "platform", "darwin"):
            from soupawhisper.backend import detect_backend_type
            assert detect_backend_type() == "darwin"

    def test_create_darwin_backend(self, mock_pynput):
        """Test creating Darwin backend."""
        from soupawhisper.backend import create_backend
        backend = create_backend("darwin")
        assert backend.__class__.__name__ == "DarwinBackend"
