"""End-to-end tests for Wayland backend."""

import os
import subprocess
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

# Skip if not on Linux/Wayland
pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or not os.environ.get("WAYLAND_DISPLAY"),
    reason="Wayland-only test"
)


class TestWaylandE2E:
    """End-to-end tests for Wayland backend."""

    def test_clipboard_roundtrip(self):
        """Test copy to clipboard and read back."""
        from soupawhisper.backend.wayland import WaylandBackend

        backend = WaylandBackend()
        test_text = "Тестовый текст 123"

        # Copy to clipboard
        backend.copy_to_clipboard(test_text)

        # Read back with wl-paste
        result = subprocess.run(
            ["wl-paste"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == test_text

    def test_ydotool_available(self):
        """Test that ydotool is installed and daemon is running."""
        # Check ydotool binary
        result = subprocess.run(["which", "ydotool"], capture_output=True)
        assert result.returncode == 0, "ydotool not installed"

        # Check if ydotoold is running or can be started
        pgrep = subprocess.run(["pgrep", "ydotoold"], capture_output=True)
        if pgrep.returncode != 0:
            pytest.skip("ydotoold not running")

    def test_evdev_keyboard_detection(self):
        """Test that keyboard devices can be found."""
        try:
            import evdev
            from soupawhisper.backend.wayland import _find_keyboard_devices

            devices = _find_keyboard_devices()
            assert len(devices) > 0, "No keyboard devices found. User may need to be in 'input' group."

            # Clean up
            for dev in devices:
                dev.close()

        except PermissionError:
            pytest.skip("No permission to access input devices. Add user to 'input' group.")

    def test_full_transcription_flow_mocked(self):
        """Test full flow with mocked API."""
        from pathlib import Path
        from soupawhisper.app import App
        from soupawhisper.backend.wayland import WaylandBackend
        from soupawhisper.config import Config

        # Create config
        config = Config(
            api_key="test-key",
            model="whisper-large-v3",
            language="ru",
            auto_type=False,  # Don't actually type
            auto_enter=False,
            notifications=False,
            backend="wayland",
        )

        # Create mock backend
        mock_backend = MagicMock(spec=WaylandBackend)

        # Create app with mock backend
        app = App(config, backend=mock_backend)

        # Mock the transcribe function
        with patch("soupawhisper.app.transcribe") as mock_transcribe:
            mock_transcribe.return_value = "Тестовая транскрипция"

            # Create a fake audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(b"RIFF" + b"\x00" * 100)  # Fake WAV header
                audio_path = Path(f.name)

            # Simulate that recording was active
            app.recorder._process = MagicMock()  # Make is_recording return True
            app.recorder._temp_file = audio_path

            # Mock stop to return the path
            with patch.object(app.recorder, 'stop', return_value=audio_path):
                app._on_release()

            # Verify clipboard was called
            mock_backend.copy_to_clipboard.assert_called_once_with("Тестовая транскрипция")

    def test_backend_detection(self):
        """Test that Wayland backend is correctly detected."""
        from soupawhisper.backend import detect_backend_type

        assert detect_backend_type() == "wayland"

    def test_config_with_wayland_backend(self):
        """Test config loading with wayland backend."""
        from soupawhisper.config import Config

        config = Config(
            api_key="test",
            backend="wayland",
        )

        assert config.backend == "wayland"


class TestWaylandBackendUnit:
    """Unit tests for Wayland backend methods."""

    def test_copy_to_clipboard_calls_wl_copy(self):
        """Test clipboard uses wl-copy."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            from soupawhisper.backend.wayland import WaylandBackend
            backend = WaylandBackend()
            backend.copy_to_clipboard("тест")

            mock_popen.assert_called_once()
            assert mock_popen.call_args[0][0] == ["wl-copy"]
            mock_process.communicate.assert_called_once_with(input="тест".encode())

    def test_type_text_smart_fallback(self):
        """Test text typing uses smart fallbacks."""
        from soupawhisper.backend.wayland import WaylandBackend

        backend = WaylandBackend()
        # First call discovers method, subsequent calls use cached method
        # Just verify it doesn't crash
        with patch("soupawhisper.backend.wayland._try_wtype", return_value=False):
            with patch("soupawhisper.backend.wayland._try_ydotool_paste", return_value=False):
                backend.type_text("тест")
                assert backend._typing_method == "clipboard"

    def test_press_key_enter(self):
        """Test pressing Enter key."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.wayland import WaylandBackend
            backend = WaylandBackend()
            backend.press_key("enter")

            mock_run.assert_called_once_with(
                ["ydotool", "key", "28:1", "28:0"],
                check=False,
            )

    def test_press_key_tab(self):
        """Test pressing Tab key."""
        with patch("subprocess.run") as mock_run:
            from soupawhisper.backend.wayland import WaylandBackend
            backend = WaylandBackend()
            backend.press_key("tab")

            mock_run.assert_called_once_with(
                ["ydotool", "key", "15:1", "15:0"],
                check=False,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
