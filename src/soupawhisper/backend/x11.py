"""X11 display backend using xclip, xdotool, and pynput."""

import subprocess
from typing import Callable

from pynput import keyboard


def _get_pynput_key(key_name: str) -> keyboard.Key | keyboard.KeyCode:
    """Map key name string to pynput key."""
    key_name = key_name.lower()
    if hasattr(keyboard.Key, key_name):
        return getattr(keyboard.Key, key_name)
    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name)
    return keyboard.Key.f12


class X11Backend:
    """X11 backend using xclip, xdotool, and pynput."""

    def __init__(self, typing_delay: int = 12):
        """Initialize X11 backend.

        Args:
            typing_delay: Delay between keystrokes in ms (0 = fastest, 12 = default)
        """
        self.typing_delay = typing_delay

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard using xclip."""
        process = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
        )
        process.communicate(input=text.encode())

    def type_text(self, text: str) -> None:
        """Type text into active window using xdotool."""
        subprocess.run(
            ["xdotool", "type", "--delay", str(self.typing_delay), "--clearmodifiers", text],
            check=False,
        )

    def press_key(self, key: str) -> None:
        """Press a single key using xdotool."""
        # Map common key names to xdotool key names
        key_map = {
            "enter": "Return",
            "tab": "Tab",
            "escape": "Escape",
            "space": "space",
            "backspace": "BackSpace",
        }
        xdotool_key = key_map.get(key.lower(), key)
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
        """Listen for hotkey using pynput. Blocks until interrupted."""
        hotkey = _get_pynput_key(key)
        is_pressed = False

        def handle_press(k: keyboard.Key) -> None:
            nonlocal is_pressed
            if k == hotkey and not is_pressed:
                is_pressed = True
                on_press()

        def handle_release(k: keyboard.Key) -> None:
            nonlocal is_pressed
            if k == hotkey and is_pressed:
                is_pressed = False
                on_release()

        with keyboard.Listener(
            on_press=handle_press,
            on_release=handle_release,
        ) as listener:
            listener.join()
