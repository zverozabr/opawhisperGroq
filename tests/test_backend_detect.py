"""Tests for backend auto-detection."""

import sys
from unittest.mock import patch

import pytest

from soupawhisper.backend import create_backend, detect_backend_type


class TestBackendDetection:
    """Tests for backend auto-detection."""

    def test_detect_wayland(self):
        """Test Wayland detection via WAYLAND_DISPLAY."""
        with patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch.object(sys, "platform", "linux"):
                assert detect_backend_type() == "wayland"

    def test_detect_x11(self):
        """Test X11 detection (no WAYLAND_DISPLAY)."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(sys, "platform", "linux"):
                assert detect_backend_type() == "x11"

    def test_detect_darwin(self):
        """Test macOS detection."""
        with patch.object(sys, "platform", "darwin"):
            assert detect_backend_type() == "darwin"

    def test_create_backend_x11(self):
        """Test creating X11 backend explicitly."""
        backend = create_backend("x11")
        assert backend.__class__.__name__ == "X11Backend"

    def test_create_backend_darwin(self):
        """Test creating Darwin backend explicitly."""
        backend = create_backend("darwin")
        assert backend.__class__.__name__ == "DarwinBackend"

    def test_create_backend_invalid(self):
        """Test invalid backend type raises error."""
        with pytest.raises(ValueError, match="Unknown backend type"):
            create_backend("invalid")
