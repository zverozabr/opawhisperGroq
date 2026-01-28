"""macOS display backend using pbcopy and pynput."""

import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable

from pynput import keyboard

from ..clipboard import copy_to_clipboard as _copy
from ..logging import get_logger
from .base import TypingMethod
from .keys import get_pynput_special_key
from .pynput_listener import PynputHotkeyListener

log = get_logger()


# =============================================================================
# Permission Status and Helper (SOLID - SRP)
# =============================================================================


@dataclass
class PermissionStatus:
    """Status of macOS permissions.

    Single Responsibility: Represents permission state.
    """

    input_monitoring: bool
    accessibility: bool

    @property
    def all_granted(self) -> bool:
        """Check if all permissions are granted."""
        return self.input_monitoring and self.accessibility

    @property
    def missing(self) -> list[str]:
        """Get list of missing permission names."""
        result = []
        if not self.input_monitoring:
            result.append("Input Monitoring")
        if not self.accessibility:
            result.append("Accessibility")
        return result


# =============================================================================
# macOS Permission Helpers
# =============================================================================


def get_permission_target() -> str:
    """Get path to add to Accessibility/Input Monitoring.

    Always returns the real Python executable path, since macOS grants
    permissions to executables, not to unsigned .app bundles.
    """
    if sys.platform != "darwin":
        return "Python"

    # Always return real Python path (resolve symlinks)
    # macOS permissions are granted to the actual executable, not the .app launcher
    return os.path.realpath(sys.executable)


def check_accessibility(prompt: bool = False) -> bool:
    """Check Accessibility permission using AX API.

    Args:
        prompt: If True, show system dialog (but app won't appear in list
                without Developer ID signing)

    Returns:
        True if permission granted, False otherwise
    """
    if sys.platform != "darwin":
        return True

    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions

        options = {"AXTrustedCheckOptionPrompt": prompt}
        return AXIsProcessTrustedWithOptions(options)
    except ImportError:
        log.debug("pyobjc not available, skipping Accessibility check")
        return True


def check_keyboard_permissions() -> bool:
    """Check if keyboard monitoring actually works using CGEventTap.

    CGEventTapCreate returns None if Input Monitoring permission is not granted.
    This is the most reliable way to check for keyboard monitoring permissions.

    Returns:
        True if Input Monitoring permission granted, False otherwise
    """
    if sys.platform != "darwin":
        return True

    try:
        from Quartz import (
            CGEventTapCreate,
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            CGEventMaskBit,
            kCGEventKeyDown,
        )

        # Try to create an event tap - returns None if no Input Monitoring permission
        def callback(proxy, event_type, event, refcon):
            return event

        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            CGEventMaskBit(kCGEventKeyDown),
            callback,
            None
        )

        if tap is None:
            log.debug("CGEventTapCreate returned None - no Input Monitoring permission")
            return False

        # Clean up
        from CoreFoundation import CFRelease
        CFRelease(tap)

        return True

    except ImportError as e:
        log.debug(f"Quartz not available: {e}")
        # Fall back to pynput check
        return _check_keyboard_permissions_pynput()
    except Exception as e:
        log.debug(f"CGEventTap check failed: {e}")
        return False


def _check_keyboard_permissions_pynput() -> bool:
    """Fallback check using pynput."""
    try:
        from pynput import keyboard

        listener = keyboard.Listener(on_press=lambda k: False)
        listener.start()

        import time
        time.sleep(0.1)

        if listener.is_alive():
            listener.stop()
            return True
        return False
    except Exception:
        return False


def needs_input_monitoring() -> bool:
    """Check if Input Monitoring permission is needed (Ventura 13.0+)."""
    if sys.platform != "darwin":
        return False
    try:
        version = tuple(map(int, platform.mac_ver()[0].split(".")[:2]))
        return version >= (13, 0)
    except Exception:
        return False


def open_accessibility_settings() -> None:
    """Open System Settings > Privacy > Accessibility."""
    if sys.platform != "darwin":
        return
    subprocess.Popen([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    ])


def open_input_monitoring_settings() -> None:
    """Open System Settings > Privacy > Input Monitoring."""
    if sys.platform != "darwin":
        return
    subprocess.Popen([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
    ])


class PermissionsHelper:
    """Unified helper for macOS permissions (SOLID - SRP).

    Single Responsibility: All permission-related operations.
    DRY: Single source of truth for permission logic, used by GUI components.
    """

    @staticmethod
    def check() -> PermissionStatus:
        """Check all macOS permissions.

        Returns:
            PermissionStatus with current state
        """
        if sys.platform != "darwin":
            return PermissionStatus(input_monitoring=True, accessibility=True)

        return PermissionStatus(
            input_monitoring=check_keyboard_permissions(),
            accessibility=check_accessibility(),
        )

    @staticmethod
    def get_python_path() -> str:
        """Get path to Python executable for adding to permissions."""
        return get_permission_target()

    @staticmethod
    def open_accessibility_with_finder() -> None:
        """Open Accessibility settings AND Finder with Python selected.

        This makes it easy to add Python to permissions:
        1. Opens Finder with Python.app selected
        2. Opens System Settings > Accessibility
        3. Copies path to clipboard

        User can then drag Python.app to Settings or use Cmd+Shift+G.
        """
        if sys.platform != "darwin":
            return

        target = get_permission_target()
        subprocess.Popen(["open", "-R", target])  # Finder with file selected
        open_accessibility_settings()
        _copy(target)  # Copy path to clipboard

    @staticmethod
    def open_input_monitoring_with_finder() -> None:
        """Open Input Monitoring settings AND Finder with Python selected."""
        if sys.platform != "darwin":
            return

        target = get_permission_target()
        subprocess.Popen(["open", "-R", target])
        open_input_monitoring_settings()
        _copy(target)

    @staticmethod
    def log_status() -> PermissionStatus:
        """Check and log permission status.

        Returns:
            PermissionStatus after logging
        """
        status = PermissionsHelper.check()

        if sys.platform == "darwin":
            log.info(
                f"Permissions: Input Monitoring={status.input_monitoring}, "
                f"Accessibility={status.accessibility}"
            )
            for missing in status.missing:
                log.warning(f"{missing} permission missing")

        return status


class DarwinBackend:
    """macOS backend using pbcopy and pynput."""

    def __init__(self, typing_delay: int = 12):
        """Initialize macOS backend.

        Args:
            typing_delay: Delay between keystrokes in ms (0 = fastest, 12 = default)
        """
        self._typing_delay = typing_delay / 1000.0  # Convert to seconds
        self._hotkey_listener = PynputHotkeyListener()
        self._keyboard = keyboard.Controller()

    def stop(self) -> None:
        """Signal the hotkey listener to stop."""
        self._hotkey_listener.stop()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard."""
        _copy(text)

    def type_text(self, text: str) -> TypingMethod:
        """Type text using pynput keyboard controller.

        Returns:
            TypingMethod.PYNPUT
        """
        for char in text:
            self._keyboard.type(char)
            if self._typing_delay > 0:
                time.sleep(self._typing_delay)
        return TypingMethod.PYNPUT

    def press_key(self, key: str) -> None:
        """Press a single key using pynput."""
        pynput_key = get_pynput_special_key(key)
        if pynput_key:
            self._keyboard.press(pynput_key)
            self._keyboard.release(pynput_key)

    def listen_hotkey(
        self,
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey using pynput. Blocks until interrupted or stop() called."""
        self._hotkey_listener.listen(key, on_press, on_release)
