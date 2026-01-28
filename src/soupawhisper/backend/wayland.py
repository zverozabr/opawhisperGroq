"""Wayland display backend with smart fallbacks."""

import shutil
import subprocess
import threading
from typing import Callable

import evdev
from evdev import ecodes

from .base import TypingMethod
from .keys import get_evdev_keycode, get_ydotool_keycode


def _find_keyboard_devices() -> list[evdev.InputDevice]:
    """Find all keyboard input devices."""
    devices = []
    for path in evdev.list_devices():
        device = evdev.InputDevice(path)
        caps = device.capabilities()
        if ecodes.EV_KEY in caps:
            key_caps = caps[ecodes.EV_KEY]
            if ecodes.KEY_A in key_caps and ecodes.KEY_ENTER in key_caps:
                devices.append(device)
    return devices


def _has_command(cmd: str) -> bool:
    """Check if command is available."""
    return shutil.which(cmd) is not None


def _try_wtype(text: str) -> bool:
    """Try typing with wtype. Returns True if successful."""
    if not _has_command("wtype"):
        return False
    result = subprocess.run(
        ["wtype", "--", text],
        capture_output=True,
    )
    # Check if wtype failed due to missing protocol
    if result.returncode != 0:
        stderr = result.stderr.decode()
        if "protocol" in stderr.lower() or "compositor" in stderr.lower():
            return False
    return result.returncode == 0


def _try_ydotool_paste() -> bool:
    """Try pasting with ydotool Ctrl+V. Returns True if successful."""
    if not _has_command("ydotool"):
        return False
    # Check if ydotoold is running
    pgrep = subprocess.run(["pgrep", "ydotoold"], capture_output=True)
    if pgrep.returncode != 0:
        return False
    # Simulate Ctrl+V
    result = subprocess.run(
        ["ydotool", "key", "-d", "20", "29:1", "47:1", "47:0", "29:0"],
        capture_output=True,
    )
    return result.returncode == 0


class WaylandBackend:
    """Wayland backend with smart fallbacks: wtype → ydotool → clipboard.

    SOLID/LSP: Constructor signature matches other backends for substitutability.
    """

    def __init__(self, typing_delay: int = 12):
        """Initialize Wayland backend.

        Args:
            typing_delay: Delay between key presses in ms (for future use).
        """
        self._typing_delay = typing_delay
        self._typing_method: TypingMethod | None = None
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Signal the hotkey listener to stop."""
        self._stop_event.set()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard."""
        from ..clipboard import copy_to_clipboard
        copy_to_clipboard(text)

    def type_text(self, text: str) -> TypingMethod:
        """Type text with smart fallbacks.

        Strategy (like Voxtype):
        1. Try wtype (best Unicode/CJK support)
        2. Try ydotool Ctrl+V (text already in clipboard)
        3. Fall back to clipboard only (user pastes manually)

        Returns:
            TypingMethod enum value
        """
        # If we already know what works, use it
        if self._typing_method == TypingMethod.WTYPE:
            if _try_wtype(text):
                return TypingMethod.WTYPE
            self._typing_method = None  # Reset, try again

        if self._typing_method == TypingMethod.YDOTOOL:
            if _try_ydotool_paste():
                return TypingMethod.YDOTOOL
            self._typing_method = None

        if self._typing_method == TypingMethod.CLIPBOARD:
            return TypingMethod.CLIPBOARD  # Just clipboard, already copied

        # First run: discover what works
        if _try_wtype(text):
            self._typing_method = TypingMethod.WTYPE
            print("[backend] Using wtype for typing")
            return TypingMethod.WTYPE

        if _try_ydotool_paste():
            self._typing_method = TypingMethod.YDOTOOL
            print("[backend] Using ydotool (Ctrl+V) for typing")
            return TypingMethod.YDOTOOL

        # Nothing works, just use clipboard
        self._typing_method = TypingMethod.CLIPBOARD
        print("[backend] Typing unavailable, use Ctrl+V to paste")
        return TypingMethod.CLIPBOARD

    def press_key(self, key: str) -> None:
        """Press a single key using ydotool."""
        key_code = get_ydotool_keycode(key)
        if key_code and _has_command("ydotool"):
            subprocess.run(
                ["ydotool", "key", f"{key_code}:1", f"{key_code}:0"],
                check=False,
            )

    def listen_hotkey(
        self,
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey using evdev. Blocks until interrupted or stop() called."""
        self._stop_event.clear()

        target_code = get_evdev_keycode(key)
        devices = _find_keyboard_devices()

        if not devices:
            raise RuntimeError(
                "No keyboard devices found. "
                "Make sure user is in 'input' group: sudo usermod -aG input $USER"
            )

        is_pressed = False

        try:
            from selectors import DefaultSelector, EVENT_READ

            selector = DefaultSelector()
            for device in devices:
                selector.register(device, EVENT_READ)

            while not self._stop_event.is_set():
                ready = selector.select(timeout=0.1)
                for key_sel, _ in ready:
                    device = key_sel.fileobj
                    for event in device.read():
                        if event.type != ecodes.EV_KEY:
                            continue
                        if event.code != target_code:
                            continue

                        if event.value == 1 and not is_pressed:
                            is_pressed = True
                            on_press()
                        elif event.value == 0 and is_pressed:
                            is_pressed = False
                            on_release()
        finally:
            for device in devices:
                device.close()
