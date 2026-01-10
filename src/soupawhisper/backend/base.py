"""Display backend protocol - abstraction for X11/Wayland."""

from typing import Protocol, Callable


class DisplayBackend(Protocol):
    """Protocol for display server backends."""

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard."""
        ...

    def type_text(self, text: str) -> None:
        """Type text into active window."""
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
