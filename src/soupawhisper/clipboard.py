"""Cross-platform clipboard utilities (DRY - single source of truth)."""

import os
import subprocess
import sys

from .logging import get_logger

log = get_logger()


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Platform support:
    - Linux X11: xclip
    - Linux Wayland: wl-copy
    - macOS: pbcopy
    - Windows: PowerShell Set-Clipboard

    Args:
        text: Text to copy

    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == "darwin":
            _copy_macos(text)
        elif sys.platform == "win32":
            _copy_windows(text)
        elif os.environ.get("WAYLAND_DISPLAY"):
            _copy_wayland(text)
        else:
            _copy_x11(text)
        return True
    except Exception as e:
        log.error(f"Failed to copy to clipboard: {e}")
        return False


CLIPBOARD_TIMEOUT = 5  # seconds


def _copy_x11(text: str) -> None:
    """Copy using xclip (X11)."""
    process = subprocess.Popen(
        ["xclip", "-selection", "clipboard"],
        stdin=subprocess.PIPE,
    )
    process.communicate(input=text.encode(), timeout=CLIPBOARD_TIMEOUT)


def _copy_wayland(text: str) -> None:
    """Copy using wl-copy (Wayland)."""
    process = subprocess.Popen(
        ["wl-copy"],
        stdin=subprocess.PIPE,
    )
    process.communicate(input=text.encode(), timeout=CLIPBOARD_TIMEOUT)


def _copy_macos(text: str) -> None:
    """Copy using pbcopy (macOS)."""
    process = subprocess.Popen(
        ["pbcopy"],
        stdin=subprocess.PIPE,
    )
    process.communicate(input=text.encode(), timeout=CLIPBOARD_TIMEOUT)


def _copy_windows(text: str) -> None:
    """Copy using PowerShell (Windows)."""
    escaped = text.replace("'", "''")
    subprocess.run(
        ["powershell", "-Command", f"Set-Clipboard -Value '{escaped}'"],
        capture_output=True,
        check=True,
    )
