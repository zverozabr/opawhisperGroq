"""Wayland display backend with smart fallbacks."""

import shutil
import subprocess
from typing import Callable

import evdev
from evdev import ecodes

# Map common key names to evdev codes
KEY_MAP = {
    "ctrl_r": ecodes.KEY_RIGHTCTRL,
    "ctrl_l": ecodes.KEY_LEFTCTRL,
    "alt_r": ecodes.KEY_RIGHTALT,
    "alt_l": ecodes.KEY_LEFTALT,
    "shift_r": ecodes.KEY_RIGHTSHIFT,
    "shift_l": ecodes.KEY_LEFTSHIFT,
    "super_r": ecodes.KEY_RIGHTMETA,
    "super_l": ecodes.KEY_LEFTMETA,
    "f1": ecodes.KEY_F1,
    "f2": ecodes.KEY_F2,
    "f3": ecodes.KEY_F3,
    "f4": ecodes.KEY_F4,
    "f5": ecodes.KEY_F5,
    "f6": ecodes.KEY_F6,
    "f7": ecodes.KEY_F7,
    "f8": ecodes.KEY_F8,
    "f9": ecodes.KEY_F9,
    "f10": ecodes.KEY_F10,
    "f11": ecodes.KEY_F11,
    "f12": ecodes.KEY_F12,
    "space": ecodes.KEY_SPACE,
    "enter": ecodes.KEY_ENTER,
    "escape": ecodes.KEY_ESC,
    "tab": ecodes.KEY_TAB,
    "backspace": ecodes.KEY_BACKSPACE,
    "caps_lock": ecodes.KEY_CAPSLOCK,
    "scroll_lock": ecodes.KEY_SCROLLLOCK,
    "print_screen": ecodes.KEY_SYSRQ,
    "pause": ecodes.KEY_PAUSE,
    "insert": ecodes.KEY_INSERT,
    "delete": ecodes.KEY_DELETE,
    "home": ecodes.KEY_HOME,
    "end": ecodes.KEY_END,
    "page_up": ecodes.KEY_PAGEUP,
    "page_down": ecodes.KEY_PAGEDOWN,
}


def _get_evdev_keycode(key_name: str) -> int:
    """Map key name to evdev keycode."""
    key_name = key_name.lower()
    if key_name in KEY_MAP:
        return KEY_MAP[key_name]
    if len(key_name) == 1:
        code_name = f"KEY_{key_name.upper()}"
        return getattr(ecodes, code_name, ecodes.KEY_F12)
    return ecodes.KEY_F12


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
    """Wayland backend with smart fallbacks: wtype → ydotool → clipboard."""

    def __init__(self):
        self._typing_method: str | None = None

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard using wl-copy."""
        process = subprocess.Popen(
            ["wl-copy"],
            stdin=subprocess.PIPE,
        )
        process.communicate(input=text.encode())

    def type_text(self, text: str) -> None:
        """Type text with smart fallbacks.

        Strategy (like Voxtype):
        1. Try wtype (best Unicode/CJK support)
        2. Try ydotool Ctrl+V (text already in clipboard)
        3. Fall back to clipboard only (user pastes manually)
        """
        # If we already know what works, use it
        if self._typing_method == "wtype":
            if _try_wtype(text):
                return
            self._typing_method = None  # Reset, try again

        if self._typing_method == "ydotool":
            if _try_ydotool_paste():
                return
            self._typing_method = None

        if self._typing_method == "clipboard":
            return  # Just clipboard, already copied

        # First run: discover what works
        if _try_wtype(text):
            self._typing_method = "wtype"
            print("[backend] Using wtype for typing")
            return

        if _try_ydotool_paste():
            self._typing_method = "ydotool"
            print("[backend] Using ydotool (Ctrl+V) for typing")
            return

        # Nothing works, just use clipboard
        self._typing_method = "clipboard"
        print("[backend] Typing unavailable, use Ctrl+V to paste")

    def press_key(self, key: str) -> None:
        """Press a single key using ydotool."""
        key_map = {
            "enter": "28",
            "tab": "15",
            "escape": "1",
            "space": "57",
            "backspace": "14",
        }
        key_code = key_map.get(key.lower())
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
        """Listen for hotkey using evdev. Blocks until interrupted."""
        target_code = _get_evdev_keycode(key)
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

            while True:
                for key_sel, _ in selector.select():
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
