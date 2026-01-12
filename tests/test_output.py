"""Tests for output module (notifications)."""

from unittest.mock import MagicMock, patch


class TestNotify:
    """Tests for notify function."""

    def test_notify_default_params(self):
        """Test notification with default parameters."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Test Title", "Test message")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]

            assert call_args[0] == "notify-send"
            assert "-a" in call_args
            assert "SoupaWhisper" in call_args
            assert "-i" in call_args
            assert "dialog-information" in call_args  # Default icon
            assert "-t" in call_args
            assert "2000" in call_args  # Default timeout
            assert "Test Title" in call_args
            assert "Test message" in call_args

    def test_notify_custom_icon(self):
        """Test notification with custom icon."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message", icon="audio-input-microphone")

            call_args = mock_run.call_args[0][0]
            assert "audio-input-microphone" in call_args

    def test_notify_custom_timeout(self):
        """Test notification with custom timeout."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message", timeout_ms=5000)

            call_args = mock_run.call_args[0][0]
            assert "5000" in call_args

    def test_notify_unicode_message(self):
        """Test notification with Unicode characters."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Привет", "Тестовое сообщение 🎤")

            call_args = mock_run.call_args[0][0]
            assert "Привет" in call_args
            assert "Тестовое сообщение 🎤" in call_args

    def test_notify_empty_message(self):
        """Test notification with empty message."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "Title" in call_args
            assert "" in call_args

    def test_notify_replacement_id(self):
        """Test notification includes replacement ID."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import _NOTIFICATION_ID, notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert "-r" in call_args
            assert str(_NOTIFICATION_ID) in call_args

    def test_notify_ubuntu_hint(self):
        """Test notification includes Ubuntu synchronous hint."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            notify("Title", "Message")

            call_args = mock_run.call_args[0][0]
            assert "-h" in call_args
            assert "string:x-canonical-private-synchronous:soupawhisper" in call_args

    def test_notify_command_fails(self):
        """Test notification handles command failure gracefully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            from soupawhisper.output import notify

            # Should not raise even if notify-send fails
            notify("Title", "Message")

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

    def test_notify_long_message(self):
        """Test notification with long message."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            long_message = "A" * 1000
            notify("Title", long_message)

            call_args = mock_run.call_args[0][0]
            assert long_message in call_args

    def test_notify_special_characters(self):
        """Test notification with special shell characters."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.output import notify

            # Special characters that might cause shell issues
            special_message = "Test $PATH && rm -rf / ; echo 'test'"
            notify("Title", special_message)

            call_args = mock_run.call_args[0][0]
            # Should pass the string as-is (subprocess handles escaping)
            assert special_message in call_args
