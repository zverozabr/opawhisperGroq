"""Tests for output module (notifications)."""

import sys
from unittest.mock import MagicMock, patch


class TestNotify:
    """Tests for notify function."""

    def test_notify_calls_subprocess(self):
        """Test notification calls subprocess.run."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Test Title", "Test message")

            mock_run.assert_called_once()

    def test_notify_capture_output(self):
        """Test notification captures output (doesn't pollute console)."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get("capture_output") is True

    def test_notify_check_false(self):
        """Test notification doesn't raise on non-zero exit."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get("check") is False

    def test_notify_command_fails(self):
        """Test notification handles command failure gracefully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            from soupawhisper.output import notify

            # Should not raise even if command fails
            notify("Title", "Message")

            mock_run.assert_called_once()


class TestNotifyMacOS:
    """Tests for macOS-specific notification behavior."""

    def test_notify_macos_uses_osascript(self):
        """Test notification on macOS uses osascript."""
        if sys.platform != "darwin":
            return  # Skip on non-macOS

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "osascript"
            assert "-e" in call_args

    def test_notify_macos_includes_title(self):
        """Test macOS notification includes title."""
        if sys.platform != "darwin":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Test Title", "Test message")

            call_args = mock_run.call_args[0][0]
            script = call_args[2]  # The AppleScript string
            assert "Test Title" in script

    def test_notify_macos_includes_message(self):
        """Test macOS notification includes message."""
        if sys.platform != "darwin":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Test message")

            call_args = mock_run.call_args[0][0]
            script = call_args[2]
            assert "Test message" in script


class TestNotifyLinux:
    """Tests for Linux-specific notification behavior."""

    def test_notify_linux_uses_notify_send(self):
        """Test notification on Linux uses notify-send."""
        if sys.platform != "linux":
            return  # Skip on non-Linux

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "notify-send"

    def test_notify_linux_includes_app_name(self):
        """Test Linux notification includes app name."""
        if sys.platform != "linux":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert "-a" in call_args
            assert "SoupaWhisper" in call_args

    def test_notify_linux_includes_icon(self):
        """Test Linux notification includes icon."""
        if sys.platform != "linux":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message", icon="audio-input-microphone")

            call_args = mock_run.call_args[0][0]
            assert "-i" in call_args
            assert "audio-input-microphone" in call_args

    def test_notify_linux_includes_timeout(self):
        """Test Linux notification includes timeout."""
        if sys.platform != "linux":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message", timeout_ms=5000)

            call_args = mock_run.call_args[0][0]
            assert "-t" in call_args
            assert "5000" in call_args

    def test_notify_linux_replacement_id(self):
        """Test Linux notification includes replacement ID."""
        if sys.platform != "linux":
            return

        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import _NOTIFICATION_ID, notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert "-r" in call_args
            assert str(_NOTIFICATION_ID) in call_args
