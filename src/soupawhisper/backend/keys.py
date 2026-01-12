"""Shared key mapping utilities for backends."""

from pynput import keyboard as pynput_keyboard


# Pynput hotkey mapping (used by X11, Darwin, Windows)
# Some keys map to multiple pynput keys (e.g., alt_r can be alt_r OR alt_gr on Linux)
PYNPUT_HOTKEY_MAP = {
    "ctrl_r": pynput_keyboard.Key.ctrl_r,
    "ctrl_l": pynput_keyboard.Key.ctrl_l,
    "ctrl": pynput_keyboard.Key.ctrl_l,  # Generic ctrl -> left ctrl
    "alt_r": pynput_keyboard.Key.alt_r,
    "alt_gr": pynput_keyboard.Key.alt_gr,
    "alt_l": pynput_keyboard.Key.alt,
    "alt": pynput_keyboard.Key.alt,  # Generic alt -> left alt
    "shift_r": pynput_keyboard.Key.shift_r,
    "shift_l": pynput_keyboard.Key.shift,
    "shift": pynput_keyboard.Key.shift,  # Generic shift -> left shift
    "super_r": pynput_keyboard.Key.cmd_r,
    "super_l": pynput_keyboard.Key.cmd,
    "super": pynput_keyboard.Key.cmd,  # Generic super -> left super
    "cmd_r": pynput_keyboard.Key.cmd_r,
    "cmd_l": pynput_keyboard.Key.cmd,
    "cmd": pynput_keyboard.Key.cmd,
    "f1": pynput_keyboard.Key.f1,
    "f2": pynput_keyboard.Key.f2,
    "f3": pynput_keyboard.Key.f3,
    "f4": pynput_keyboard.Key.f4,
    "f5": pynput_keyboard.Key.f5,
    "f6": pynput_keyboard.Key.f6,
    "f7": pynput_keyboard.Key.f7,
    "f8": pynput_keyboard.Key.f8,
    "f9": pynput_keyboard.Key.f9,
    "f10": pynput_keyboard.Key.f10,
    "f11": pynput_keyboard.Key.f11,
    "f12": pynput_keyboard.Key.f12,
    "space": pynput_keyboard.Key.space,
    "enter": pynput_keyboard.Key.enter,
    "tab": pynput_keyboard.Key.tab,
    "escape": pynput_keyboard.Key.esc,
    "pause": pynput_keyboard.Key.pause,
}

# Pynput special key mapping (for press_key)
PYNPUT_SPECIAL_KEYS = {
    "enter": pynput_keyboard.Key.enter,
    "tab": pynput_keyboard.Key.tab,
    "escape": pynput_keyboard.Key.esc,
    "space": pynput_keyboard.Key.space,
    "backspace": pynput_keyboard.Key.backspace,
}


# Keys that can be reported as multiple different pynput keys
# On Linux, Right Alt is often configured as AltGr for special characters
PYNPUT_KEY_ALIASES = {
    "alt_r": [pynput_keyboard.Key.alt_r, pynput_keyboard.Key.alt_gr],
    "alt_gr": [pynput_keyboard.Key.alt_gr, pynput_keyboard.Key.alt_r],
}


def get_pynput_key(key_name: str) -> pynput_keyboard.Key | pynput_keyboard.KeyCode:
    """Map key name string to pynput key.

    Supports single keys (f9, ctrl_r) and combos (ctrl+g, alt+f9).

    Args:
        key_name: Key name like 'ctrl_r', 'f12', 'ctrl+g', or single character

    Returns:
        pynput Key or KeyCode
    """
    key_name = key_name.lower()

    # Handle combo (e.g., "ctrl+g") - return the key part
    if "+" in key_name:
        key_name = key_name.split("+")[-1]

    # Check hotkey map first
    if key_name in PYNPUT_HOTKEY_MAP:
        return PYNPUT_HOTKEY_MAP[key_name]

    # Check if it's a Key attribute
    if hasattr(pynput_keyboard.Key, key_name):
        return getattr(pynput_keyboard.Key, key_name)

    # Single character
    if len(key_name) == 1:
        return pynput_keyboard.KeyCode.from_char(key_name)

    # Default fallback
    return pynput_keyboard.Key.f12


def get_pynput_keys(key_name: str) -> list[pynput_keyboard.Key | pynput_keyboard.KeyCode]:
    """Get ALL possible pynput keys for a given key name.
    
    Some keys (like alt_r) can be reported as different keys depending on
    keyboard layout. This returns all possible variants.

    Args:
        key_name: Key name like 'alt_r', 'ctrl_r', etc.

    Returns:
        List of pynput keys that should all trigger this hotkey
    """
    key_name = key_name.lower()

    # Handle combo (e.g., "ctrl+g") - return the key part
    if "+" in key_name:
        key_name = key_name.split("+")[-1]

    # Check if this key has aliases
    if key_name in PYNPUT_KEY_ALIASES:
        return PYNPUT_KEY_ALIASES[key_name]

    # Otherwise return single key in a list
    return [get_pynput_key(key_name)]


def get_pynput_special_key(key_name: str) -> pynput_keyboard.Key | None:
    """Get pynput key for special keys like enter, tab, etc.

    Args:
        key_name: Key name like 'enter', 'tab', 'escape'

    Returns:
        pynput Key or None if not found
    """
    return PYNPUT_SPECIAL_KEYS.get(key_name.lower())


# Valid hotkey names for config validation
# Used by config.py to validate hotkey settings
PYNPUT_KEY_TO_NAME: dict[pynput_keyboard.Key, str] = {
    pynput_keyboard.Key.ctrl_r: "ctrl_r",
    pynput_keyboard.Key.ctrl_l: "ctrl_l",
    pynput_keyboard.Key.ctrl: "ctrl_l",
    pynput_keyboard.Key.alt_gr: "alt_gr",
    pynput_keyboard.Key.alt_r: "alt_r",
    pynput_keyboard.Key.alt: "alt_l",
    pynput_keyboard.Key.alt_l: "alt_l",
    pynput_keyboard.Key.shift_r: "shift_r",
    pynput_keyboard.Key.shift: "shift_l",
    pynput_keyboard.Key.cmd_r: "super_r",
    pynput_keyboard.Key.cmd: "super_l",
    pynput_keyboard.Key.f1: "f1",
    pynput_keyboard.Key.f2: "f2",
    pynput_keyboard.Key.f3: "f3",
    pynput_keyboard.Key.f4: "f4",
    pynput_keyboard.Key.f5: "f5",
    pynput_keyboard.Key.f6: "f6",
    pynput_keyboard.Key.f7: "f7",
    pynput_keyboard.Key.f8: "f8",
    pynput_keyboard.Key.f9: "f9",
    pynput_keyboard.Key.f10: "f10",
    pynput_keyboard.Key.f11: "f11",
    pynput_keyboard.Key.f12: "f12",
    pynput_keyboard.Key.f13: "f13",
    pynput_keyboard.Key.f14: "f14",
    pynput_keyboard.Key.f15: "f15",
    pynput_keyboard.Key.f16: "f16",
    pynput_keyboard.Key.f17: "f17",
    pynput_keyboard.Key.f18: "f18",
    pynput_keyboard.Key.f19: "f19",
    pynput_keyboard.Key.f20: "f20",
    pynput_keyboard.Key.space: "space",
    pynput_keyboard.Key.enter: "enter",
    pynput_keyboard.Key.tab: "tab",
    pynput_keyboard.Key.esc: "escape",
    pynput_keyboard.Key.backspace: "backspace",
    pynput_keyboard.Key.caps_lock: "caps_lock",
    pynput_keyboard.Key.num_lock: "num_lock",
    pynput_keyboard.Key.scroll_lock: "scroll_lock",
    pynput_keyboard.Key.print_screen: "print_screen",
    pynput_keyboard.Key.pause: "pause",
    pynput_keyboard.Key.insert: "insert",
    pynput_keyboard.Key.delete: "delete",
    pynput_keyboard.Key.home: "home",
    pynput_keyboard.Key.end: "end",
    pynput_keyboard.Key.page_up: "page_up",
    pynput_keyboard.Key.page_down: "page_down",
    pynput_keyboard.Key.menu: "menu",
}
