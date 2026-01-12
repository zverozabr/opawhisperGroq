"""Windows backend using pynput and pyperclip."""

import time
from typing import Callable

from pynput import keyboard

from ..clipboard import copy_to_clipboard as _copy
from .base import TypingMethod
from .keys import get_pynput_special_key
from .pynput_listener import PynputHotkeyListener


class WindowsBackend:
    """Windows display backend using pynput."""

    def __init__(self, typing_delay: int = 12):
        """Initialize Windows backend.

        Args:
            typing_delay: Delay between keystrokes in milliseconds
        """
        self._typing_delay = typing_delay / 1000.0  # Convert to seconds
        self._hotkey_listener = PynputHotkeyListener()
        self._keyboard = keyboard.Controller()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        _copy(text)

    def type_text(self, text: str) -> TypingMethod:
        """Type text using pynput.

        Returns:
            TypingMethod.PYNPUT
        """
        for char in text:
            self._keyboard.type(char)
            if self._typing_delay > 0:
                time.sleep(self._typing_delay)
        return TypingMethod.PYNPUT

    def press_key(self, key: str) -> None:
        """Press a special key."""
        pynput_key = get_pynput_special_key(key)
        if pynput_key:
            self._keyboard.press(pynput_key)
            self._keyboard.release(pynput_key)

    def listen_hotkey(
        self,
        hotkey: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey press/release events.

        Args:
            hotkey: Hotkey identifier (e.g., 'ctrl_r', 'f12')
            on_press: Callback when hotkey is pressed
            on_release: Callback when hotkey is released
        """
        self._hotkey_listener.listen(hotkey, on_press, on_release)

    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._hotkey_listener.stop()
