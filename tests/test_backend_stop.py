"""Tests for backend stop functionality."""

import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Wayland only on Linux")
class TestWaylandBackendStop:
    """Tests for WaylandBackend.stop()."""

    def test_stop_sets_event(self):
        """Test that stop() sets the stop event."""
        from soupawhisper.backend.wayland import WaylandBackend

        backend = WaylandBackend()
        assert not backend._stop_event.is_set()

        backend.stop()

        assert backend._stop_event.is_set()

    def test_stop_event_cleared_on_listen(self):
        """Test that stop event is cleared when listen_hotkey starts."""
        from soupawhisper.backend.wayland import WaylandBackend

        backend = WaylandBackend()
        backend._stop_event.set()

        # Mock _find_keyboard_devices to return empty list (will raise error)
        with patch("soupawhisper.backend.wayland._find_keyboard_devices", return_value=[]):
            with pytest.raises(RuntimeError, match="No keyboard devices found"):
                backend.listen_hotkey("ctrl_r", lambda: None, lambda: None)

        # Even though it raised, stop_event should have been cleared
        assert not backend._stop_event.is_set()


class TestX11BackendStop:
    """Tests for X11Backend.stop()."""

    def test_stop_without_listener(self):
        """Test stop() when listener not started."""
        with patch("soupawhisper.backend.pynput_listener.keyboard"):
            from soupawhisper.backend.x11 import X11Backend

            backend = X11Backend()
            # Internal listener in PynputHotkeyListener is None
            assert backend._hotkey_listener._listener is None

            # Should not raise
            backend.stop()

    def test_stop_calls_listener_stop(self):
        """Test that stop() calls listener.stop()."""
        with patch("soupawhisper.backend.pynput_listener.keyboard"):
            from soupawhisper.backend.x11 import X11Backend

            backend = X11Backend()
            mock_listener = MagicMock()
            backend._hotkey_listener._listener = mock_listener

            backend.stop()

            mock_listener.stop.assert_called_once()


class TestDarwinBackendStop:
    """Tests for DarwinBackend.stop()."""

    def test_stop_without_listener(self):
        """Test stop() when listener not started."""
        with patch("soupawhisper.backend.pynput_listener.keyboard"):
            with patch("soupawhisper.backend.darwin.keyboard"):
                from soupawhisper.backend.darwin import DarwinBackend

                backend = DarwinBackend()
                # Internal listener in PynputHotkeyListener is None
                assert backend._hotkey_listener._listener is None

                # Should not raise
                backend.stop()

    def test_stop_calls_listener_stop(self):
        """Test that stop() calls listener.stop()."""
        with patch("soupawhisper.backend.pynput_listener.keyboard"):
            with patch("soupawhisper.backend.darwin.keyboard"):
                from soupawhisper.backend.darwin import DarwinBackend

                backend = DarwinBackend()
                mock_listener = MagicMock()
                backend._hotkey_listener._listener = mock_listener

                backend.stop()

                mock_listener.stop.assert_called_once()


class TestTypeTextReturnsMethod:
    """Tests that type_text() returns the method used."""

    def test_x11_returns_xdotool(self):
        """Test X11Backend.type_text() returns 'xdotool'."""
        with patch("soupawhisper.backend.x11.subprocess.run"):
            from soupawhisper.backend.x11 import X11Backend

            backend = X11Backend()
            method = backend.type_text("test")

            assert method == "xdotool"

    def test_darwin_returns_pynput(self):
        """Test DarwinBackend.type_text() returns 'pynput'."""
        with patch("soupawhisper.backend.darwin.keyboard"):
            from soupawhisper.backend.darwin import DarwinBackend

            backend = DarwinBackend()
            method = backend.type_text("test")

            assert method == "pynput"

    @pytest.mark.skipif(sys.platform != "linux", reason="Wayland only on Linux")
    def test_wayland_returns_method(self):
        """Test WaylandBackend.type_text() returns method used."""
        # Test wtype path
        with patch("soupawhisper.backend.wayland._try_wtype", return_value=True):
            from soupawhisper.backend.wayland import WaylandBackend

            backend = WaylandBackend()
            method = backend.type_text("test")

            assert method == "wtype"

    @pytest.mark.skipif(sys.platform != "linux", reason="Wayland only on Linux")
    def test_wayland_falls_back_to_clipboard(self):
        """Test WaylandBackend falls back to clipboard."""
        with patch("soupawhisper.backend.wayland._try_wtype", return_value=False):
            with patch("soupawhisper.backend.wayland._try_ydotool_paste", return_value=False):
                from soupawhisper.backend.wayland import WaylandBackend

                backend = WaylandBackend()
                backend._typing_method = None  # Reset cache
                method = backend.type_text("test")

                assert method == "clipboard"
