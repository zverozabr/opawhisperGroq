"""X11 display backend using xclip, xdotool, and pynput."""

import subprocess
from typing import Callable

from ..clipboard import copy_to_clipboard as _copy
from .base import TypingMethod
from .keys import get_xdotool_key
from .pynput_listener import PynputHotkeyListener


class X11Backend:
    """X11 backend using xclip, xdotool, and pynput."""

    def __init__(self, typing_delay: int = 12):
        """Initialize X11 backend.

        Args:
            typing_delay: Delay between keystrokes in ms (0 = fastest, 12 = default)
        """
        self.typing_delay = typing_delay
        self._hotkey_listener = PynputHotkeyListener()

    def stop(self) -> None:
        """Signal the hotkey listener to stop."""
        self._hotkey_listener.stop()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard."""
        _copy(text)

    def type_text(self, text: str) -> TypingMethod:
        """Type text into active window using xdotool.

        Returns:
            TypingMethod.XDOTOOL
        """
        subprocess.run(
            ["xdotool", "type", "--delay", str(self.typing_delay), "--clearmodifiers", "--", text],
            check=False,
        )
        return TypingMethod.XDOTOOL

    def press_key(self, key: str) -> None:
        """Press a single key using xdotool."""
        xdotool_key = get_xdotool_key(key)
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", xdotool_key],
            check=False,
        )

    def listen_hotkey(
        self,
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey using pynput. Blocks until interrupted or stop() called."""
        self._hotkey_listener.listen(key, on_press, on_release)
