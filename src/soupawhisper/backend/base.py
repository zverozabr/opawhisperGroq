"""Display backend protocol - abstraction for X11/Wayland."""

from enum import Enum
from typing import Callable, Protocol


class TypingMethod(str, Enum):
    """Method used for typing text into windows."""

    XDOTOOL = "xdotool"
    WTYPE = "wtype"
    YDOTOOL = "ydotool"
    PYNPUT = "pynput"
    CLIPBOARD = "clipboard"  # Manual paste required
    NONE = "none"


class DisplayBackend(Protocol):
    """Protocol for display server backends."""

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard."""
        ...

    def type_text(self, text: str) -> TypingMethod:
        """Type text into active window.

        Returns:
            TypingMethod enum value indicating how text was typed
        """
        ...

    def press_key(self, key: str) -> None:
        """Press a single key (e.g., 'enter', 'tab', 'escape')."""
        ...

    def listen_hotkey(
        self,
        key: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        """Listen for hotkey press/release events. Blocks until interrupted."""
        ...

    def stop(self) -> None:
        """Signal the hotkey listener to stop."""
        ...
