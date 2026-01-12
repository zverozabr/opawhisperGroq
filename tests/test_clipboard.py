"""Tests for shared clipboard module."""

import sys
from unittest.mock import MagicMock, patch


class TestClipboard:
    """Tests for clipboard copy functionality."""

    def test_copy_x11(self):
        """Test copy on X11 (Linux without Wayland)."""
        with patch.object(sys, "platform", "linux"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("subprocess.Popen") as mock_popen:
                    mock_process = MagicMock()
                    mock_popen.return_value = mock_process

                    from soupawhisper.clipboard import copy_to_clipboard
                    result = copy_to_clipboard("test")

                    assert result is True
                    mock_popen.assert_called_once()
                    assert mock_popen.call_args[0][0] == ["xclip", "-selection", "clipboard"]
                    mock_process.communicate.assert_called_once_with(input=b"test", timeout=5)

    def test_copy_wayland(self):
        """Test copy on Wayland."""
        with patch.object(sys, "platform", "linux"):
            with patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"}):
                with patch("subprocess.Popen") as mock_popen:
                    mock_process = MagicMock()
                    mock_popen.return_value = mock_process

                    from soupawhisper.clipboard import copy_to_clipboard
                    result = copy_to_clipboard("тест")

                    assert result is True
                    mock_popen.assert_called_once()
                    assert mock_popen.call_args[0][0] == ["wl-copy"]

    def test_copy_macos(self):
        """Test copy on macOS."""
        with patch.object(sys, "platform", "darwin"):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                from soupawhisper.clipboard import copy_to_clipboard
                result = copy_to_clipboard("hello")

                assert result is True
                mock_popen.assert_called_once()
                assert mock_popen.call_args[0][0] == ["pbcopy"]

    def test_copy_windows(self):
        """Test copy on Windows."""
        with patch.object(sys, "platform", "win32"):
            with patch("subprocess.run") as mock_run:
                from soupawhisper.clipboard import copy_to_clipboard
                result = copy_to_clipboard("test")

                assert result is True
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "powershell"

    def test_copy_windows_escapes_quotes(self):
        """Test Windows copy escapes single quotes."""
        with patch.object(sys, "platform", "win32"):
            with patch("subprocess.run") as mock_run:
                from soupawhisper.clipboard import copy_to_clipboard
                copy_to_clipboard("it's a test")

                call_args = mock_run.call_args[0][0]
                # Single quote should be escaped as ''
                assert "it''s a test" in call_args[2]

    def test_copy_returns_false_on_error(self):
        """Test copy returns False on error."""
        with patch.object(sys, "platform", "linux"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("subprocess.Popen", side_effect=Exception("fail")):
                    from soupawhisper.clipboard import copy_to_clipboard
                    result = copy_to_clipboard("test")

                    assert result is False
