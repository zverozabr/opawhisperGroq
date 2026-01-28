"""Hotkey capture widget with SET button and key interception.

Single Responsibility: Capture and display hotkey with interactive SET mode.
"""

from typing import Callable, Optional

from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Static


# Human-readable hotkey names
HOTKEY_NAMES = {
    "ctrl_r": "Right Ctrl",
    "ctrl_l": "Left Ctrl",
    "alt_r": "Right Alt",
    "alt_l": "Left Alt",
    "super_r": "Right Cmd",
    "super_l": "Left Cmd",
    "f12": "F12",
    "f11": "F11",
    "f10": "F10",
    "f9": "F9",
    "space": "Space",
}


def format_hotkey(hotkey: str) -> str:
    """Format hotkey string for human-readable display.

    Args:
        hotkey: Internal hotkey string (e.g., "ctrl_r", "alt_r+f12")

    Returns:
        Human-readable string (e.g., "Right Ctrl", "Right Alt + F12")
    """
    if not hotkey:
        return "None"

    if "+" in hotkey:
        parts = hotkey.split("+")
        formatted = [HOTKEY_NAMES.get(p, p.upper()) for p in parts]
        return " + ".join(formatted)
    else:
        return HOTKEY_NAMES.get(hotkey, hotkey.upper())


class HotkeyCapture(Horizontal):
    """Widget for capturing hotkey with SET button.

    Displays current hotkey and allows changing via key capture.
    """

    DEFAULT_CSS = """
    HotkeyCapture {
        height: 3;
        width: 1fr;
    }

    HotkeyCapture #hotkey-display {
        width: 1fr;
        padding: 0 1;
        content-align: left middle;
    }

    HotkeyCapture #hotkey-display.-capturing {
        background: $warning;
        color: $text;
    }

    HotkeyCapture #set-hotkey-btn {
        width: 10;
        min-width: 8;
    }
    """

    is_capturing: reactive[bool] = reactive(False)

    def __init__(
        self,
        hotkey: str = "ctrl_r",
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        """Initialize hotkey capture widget.

        Args:
            hotkey: Current hotkey string (e.g., "ctrl_r", "alt_r+f12").
            on_change: Callback when hotkey changes.
        """
        super().__init__(**kwargs)
        self._hotkey = hotkey
        self._on_change = on_change
        self._listener = None
        self._pressed_keys: set[str] = set()
        self._captured_combination: list[str] = []

    def compose(self):
        """Create child widgets."""
        yield Static(format_hotkey(self._hotkey), id="hotkey-display")
        yield Button("SET", id="set-hotkey-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "set-hotkey-btn":
            if self.is_capturing:
                self._cancel_capture()
            else:
                self._start_capture()

    def _start_capture(self) -> None:
        """Enter capture mode."""
        self.is_capturing = True
        self._pressed_keys.clear()
        self._captured_combination.clear()
        self._update_display()

        # Pause main hotkey listener to avoid triggering recording
        self._pause_main_listener()

        self._start_key_listener()

    def _pause_main_listener(self) -> None:
        """Pause the main app hotkey listener."""
        try:
            if hasattr(self.app, "pause_hotkey_listener"):
                self.app.pause_hotkey_listener()
        except Exception:
            pass

    def _resume_main_listener(self) -> None:
        """Resume the main app hotkey listener."""
        try:
            if hasattr(self.app, "resume_hotkey_listener"):
                self.app.resume_hotkey_listener()
        except Exception:
            pass

    def _cancel_capture(self) -> None:
        """Exit capture mode without saving."""
        self._stop_key_listener()
        self.is_capturing = False
        self._update_display()

        # Resume main hotkey listener
        self._resume_main_listener()

    def _on_key_captured(self, hotkey: str) -> None:
        """Handle captured hotkey.

        Args:
            hotkey: Captured hotkey string
        """
        self._stop_key_listener()
        self.is_capturing = False
        self._hotkey = hotkey
        self._update_display()

        # Resume main hotkey listener
        self._resume_main_listener()

        if self._on_change:
            self._on_change(hotkey)

    def _update_display(self) -> None:
        """Update the display label."""
        try:
            label = self.query_one("#hotkey-display", Static)
            btn = self.query_one("#set-hotkey-btn", Button)

            if self.is_capturing:
                if self._pressed_keys:
                    # Show current combination in realtime
                    combo = "+".join(sorted(self._pressed_keys))
                    label.update(format_hotkey(combo) + " ...")
                else:
                    label.update("Press key...")
                label.add_class("-capturing")
                btn.label = "Cancel"
            else:
                label.update(format_hotkey(self._hotkey))
                label.remove_class("-capturing")
                btn.label = "SET"
        except Exception:
            pass

    def _on_key_press(self, hotkey: str) -> None:
        """Handle key press during capture.

        Args:
            hotkey: Pressed hotkey string (e.g., "alt_r", "f12")
        """
        if not self.is_capturing:
            return

        self._pressed_keys.add(hotkey)
        if hotkey not in self._captured_combination:
            self._captured_combination.append(hotkey)

        # Update display to show current combination
        self._update_display()

    def _on_key_release(self, hotkey: str) -> None:
        """Handle key release during capture.

        When all keys are released, finalize the capture.

        Args:
            hotkey: Released hotkey string
        """
        if not self.is_capturing:
            return

        self._pressed_keys.discard(hotkey)

        # When all keys released, finalize capture
        if not self._pressed_keys and self._captured_combination:
            self._finalize_capture()

    def _finalize_capture(self) -> None:
        """Finalize capture with current combination."""
        if not self._captured_combination:
            return

        # Sort for consistent ordering (modifiers first, then keys)
        def key_order(k: str) -> int:
            # Modifiers come first
            if k.startswith("ctrl") or k.startswith("alt") or k.startswith("super"):
                return 0
            return 1

        sorted_keys = sorted(self._captured_combination, key=key_order)
        hotkey = "+".join(sorted_keys)

        self._on_key_captured(hotkey)

    def _start_key_listener(self) -> None:
        """Start listening for key presses using pynput."""
        try:
            from pynput import keyboard

            def on_press(key):
                hotkey = self._key_to_hotkey(key)
                if hotkey:
                    # Use call_from_thread to safely update UI
                    self.app.call_from_thread(self._on_key_press, hotkey)
                return True  # Continue listening

            def on_release(key):
                hotkey = self._key_to_hotkey(key)
                if hotkey:
                    self.app.call_from_thread(self._on_key_release, hotkey)
                return True  # Continue listening

            self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener.start()
        except ImportError:
            # pynput not available, just cancel
            self._cancel_capture()

    def _stop_key_listener(self) -> None:
        """Stop the key listener."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _key_to_hotkey(self, key) -> Optional[str]:
        """Convert pynput key to hotkey string.

        Args:
            key: pynput Key object

        Returns:
            Hotkey string or None if not a valid hotkey
        """
        try:
            from pynput.keyboard import Key

            # Map pynput keys to hotkey strings
            key_map = {
                Key.ctrl_r: "ctrl_r",
                Key.ctrl_l: "ctrl_l",
                Key.alt_r: "alt_r",
                Key.alt_l: "alt_l",
                Key.cmd_r: "super_r",
                Key.cmd_l: "super_l",
                Key.f12: "f12",
                Key.f11: "f11",
                Key.f10: "f10",
                Key.f9: "f9",
                Key.space: "space",
            }

            return key_map.get(key)
        except Exception:
            return None

    @property
    def value(self) -> str:
        """Get current hotkey value."""
        return self._hotkey
