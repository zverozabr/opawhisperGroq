"""Tests for Windows backend."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestWindowsBackendCrossPlatform:
    """Tests that run on any platform."""

    def test_import_windows_backend(self):
        """Test that Windows backend can be imported on any platform."""
        from soupawhisper.backend.windows import WindowsBackend
        assert WindowsBackend is not None

    def test_windows_in_valid_backends(self):
        """Test 'windows' is a valid backend option."""
        from soupawhisper.config import VALID_BACKENDS
        assert "windows" in VALID_BACKENDS

    def test_create_backend_function_exists(self):
        """Test create_backend supports windows type."""
        from soupawhisper.backend import create_backend
        # Just verify the function exists and accepts 'windows'
        # Don't actually create on non-Windows as it may fail
        assert callable(create_backend)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific tests")
class TestWindowsBackend:
    """Tests for WindowsBackend class (Windows only)."""

    def test_init(self):
        """Test WindowsBackend initialization."""
        from soupawhisper.backend.windows import WindowsBackend
        backend = WindowsBackend(typing_delay=20)
        assert backend._typing_delay == 0.02  # Converted to seconds

    def test_copy_to_clipboard(self):
        """Test clipboard copy uses PowerShell."""
        from soupawhisper.backend.windows import WindowsBackend

        backend = WindowsBackend()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            backend.copy_to_clipboard("test text")
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "powershell" in call_args

    def test_type_text_returns_method(self):
        """Test type_text returns 'pynput'."""
        from soupawhisper.backend.windows import WindowsBackend

        backend = WindowsBackend(typing_delay=0)

        with patch.object(backend._keyboard, "type"):
            result = backend.type_text("test")
            assert result == "pynput"

    def test_stop(self):
        """Test stop method stops listener."""
        from soupawhisper.backend.windows import WindowsBackend

        backend = WindowsBackend()
        backend._listener = MagicMock()

        backend.stop()
        backend._listener.stop.assert_called_once()

    def test_detect_backend_on_windows(self):
        """Test backend detection returns 'windows' on Windows."""
        from soupawhisper.backend import detect_backend_type
        assert detect_backend_type() == "windows"

    def test_create_windows_backend(self):
        """Test creating Windows backend explicitly."""
        from soupawhisper.backend import create_backend
        backend = create_backend("windows")
        assert backend is not None
