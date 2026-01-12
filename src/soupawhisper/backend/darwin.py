"""macOS display backend using pbcopy and pynput."""

import time
from typing import Callable

from pynput import keyboard

from ..clipboard import copy_to_clipboard as _copy
from .base import TypingMethod
from .keys import get_pynput_special_key
from .pynput_listener import PynputHotkeyListener


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
