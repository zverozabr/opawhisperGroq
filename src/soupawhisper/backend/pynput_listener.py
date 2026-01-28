"""Shared pynput hotkey listener for X11, Darwin, and Windows backends."""

import sys
from typing import Callable

from pynput import keyboard

from soupawhisper.logging import get_logger

from .key_compare import get_key_comparer
from .keys import get_pynput_keys

log = get_logger()


class PynputHotkeyListener:
    """Reusable pynput hotkey listener with press/release callbacks.

    Usage:
        listener = PynputHotkeyListener()
        listener.listen("ctrl_r", on_press, on_release)  # Blocks
        # From another thread:
        listener.stop()
    """

    def __init__(self):
        self._listener: keyboard.Listener | None = None
        self._stopped = False
        self._comparer = get_key_comparer()

    def stop(self) -> None:
        """Signal the hotkey listener to stop."""
        self._stopped = True
        if self._listener:
            self._listener.stop()

    def listen(
        self,
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey using pynput. Blocks until interrupted or stop() called.

        Args:
            key: Key name (e.g., 'ctrl_r', 'f12', 'alt_r')
            on_press: Callback when key is pressed
            on_release: Callback when key is released
        """
        # Get all possible key variants (e.g., alt_r can be alt_r OR alt_gr)
        hotkeys = get_pynput_keys(key)
        is_pressed = False
        self._stopped = False

        def handle_press(k: keyboard.Key) -> None:
            nonlocal is_pressed
            # Use comparer for platform-specific key matching (macOS needs vk comparison)
            if any(self._comparer.keys_equal(k, hk) for hk in hotkeys) and not is_pressed:
                is_pressed = True
                on_press()

        def handle_release(k: keyboard.Key) -> None:
            nonlocal is_pressed
            # Use comparer for platform-specific key matching (macOS needs vk comparison)
            if any(self._comparer.keys_equal(k, hk) for hk in hotkeys) and is_pressed:
                is_pressed = False
                on_release()

        try:
            self._listener = keyboard.Listener(
                on_press=handle_press,
                on_release=handle_release,
            )
            self._listener.start()
        except Exception as e:
            log.error(f"Failed to start hotkey listener: {e}")
            if sys.platform == "darwin":
                log.error(
                    "On macOS, grant Accessibility permissions: "
                    "System Settings → Privacy & Security → Accessibility"
                )
            raise

        # Check if listener actually started
        if not self._listener.is_alive():
            log.error("Hotkey listener failed to start")
            if sys.platform == "darwin":
                log.error(
                    "Grant Accessibility permissions: "
                    "System Settings → Privacy & Security → Accessibility"
                )

        try:
            # Use timeout-based join to allow checking stop flag
            while not self._stopped and self._listener.is_alive():
                self._listener.join(timeout=0.5)
        finally:
            if self._listener:
                self._listener.stop()
            self._listener = None
