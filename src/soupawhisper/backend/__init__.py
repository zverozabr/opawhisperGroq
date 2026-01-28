"""Display backend auto-detection and factory."""

import os
import sys

from .base import DisplayBackend, TypingMethod

__all__ = ["DisplayBackend", "TypingMethod", "create_backend", "detect_backend_type"]


def detect_backend_type() -> str:
    """Detect the appropriate backend type for current platform."""
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "linux":
        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        return "x11"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def create_backend(backend_type: str = "auto", typing_delay: int = 12) -> DisplayBackend:
    """Create a display backend instance.

    Args:
        backend_type: One of "auto", "x11", "wayland", "darwin", "windows"
        typing_delay: Delay between keystrokes in ms

    Returns:
        DisplayBackend instance
    """
    if backend_type == "auto":
        backend_type = detect_backend_type()

    if backend_type == "x11":
        from .x11 import X11Backend
        return X11Backend(typing_delay=typing_delay)
    if backend_type == "wayland":
        from .wayland import WaylandBackend
        return WaylandBackend(typing_delay=typing_delay)
    if backend_type == "darwin":
        from .darwin import DarwinBackend
        return DarwinBackend(typing_delay=typing_delay)
    if backend_type == "windows":
        from .windows import WindowsBackend
        return WindowsBackend(typing_delay=typing_delay)

    raise ValueError(f"Unknown backend type: {backend_type}")
