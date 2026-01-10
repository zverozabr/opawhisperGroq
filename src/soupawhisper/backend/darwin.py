"""macOS display backend using pbcopy and pynput."""

import subprocess
from typing import Callable

from pynput import keyboard


def _get_pynput_key(key_name: str) -> keyboard.Key | keyboard.KeyCode:
    """Map key name string to pynput key."""
    key_name = key_name.lower()
    # macOS uses cmd instead of super
    if key_name in ("super_r", "cmd_r"):
        return keyboard.Key.cmd_r
    if key_name in ("super_l", "cmd_l", "cmd"):
        return keyboard.Key.cmd
    if hasattr(keyboard.Key, key_name):
        return getattr(keyboard.Key, key_name)
    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name)
    return keyboard.Key.f12


class DarwinBackend:
    """macOS backend using pbcopy and pynput."""

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard using pbcopy."""
        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
        )
        process.communicate(input=text.encode())

    def type_text(self, text: str) -> None:
        """Type text using pynput keyboard controller."""
        controller = keyboard.Controller()
        controller.type(text)

    def press_key(self, key: str) -> None:
        """Press a single key using pynput."""
        key_map = {
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "escape": keyboard.Key.esc,
            "space": keyboard.Key.space,
            "backspace": keyboard.Key.backspace,
        }
        pynput_key = key_map.get(key.lower())
        if pynput_key:
            controller = keyboard.Controller()
            controller.press(pynput_key)
            controller.release(pynput_key)

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
