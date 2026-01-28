"""Shared key mapping utilities for backends."""

from pynput import keyboard as pynput_keyboard


def _safe_key(name: str) -> pynput_keyboard.Key | None:
    """Safely get a pynput Key attribute (some keys don't exist on all platforms)."""
    return getattr(pynput_keyboard.Key, name, None)


# Pynput hotkey mapping (used by X11, Darwin, Windows)
# Some keys map to multiple pynput keys (e.g., alt_r can be alt_r OR alt_gr on Linux)
_PYNPUT_HOTKEY_MAP_RAW = {
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
    "pause": _safe_key("pause"),  # Not available on macOS
}
# Filter out None values (keys not available on this platform)
PYNPUT_HOTKEY_MAP = {k: v for k, v in _PYNPUT_HOTKEY_MAP_RAW.items() if v is not None}

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
# Built dynamically to handle platform-specific keys (some don't exist on macOS)
_KEY_TO_NAME_SPEC = [
    # Modifiers
    ("ctrl_r", "ctrl_r"), ("ctrl_l", "ctrl_l"), ("ctrl", "ctrl_l"),
    ("alt_gr", "alt_gr"), ("alt_r", "alt_r"), ("alt", "alt_l"), ("alt_l", "alt_l"),
    ("shift_r", "shift_r"), ("shift", "shift_l"),
    ("cmd_r", "super_r"), ("cmd", "super_l"),
    # Function keys
    ("f1", "f1"), ("f2", "f2"), ("f3", "f3"), ("f4", "f4"), ("f5", "f5"),
    ("f6", "f6"), ("f7", "f7"), ("f8", "f8"), ("f9", "f9"), ("f10", "f10"),
    ("f11", "f11"), ("f12", "f12"), ("f13", "f13"), ("f14", "f14"), ("f15", "f15"),
    ("f16", "f16"), ("f17", "f17"), ("f18", "f18"), ("f19", "f19"), ("f20", "f20"),
    # Common keys
    ("space", "space"), ("enter", "enter"), ("tab", "tab"),
    ("esc", "escape"), ("backspace", "backspace"),
    ("caps_lock", "caps_lock"), ("delete", "delete"),
    ("home", "home"), ("end", "end"), ("page_up", "page_up"), ("page_down", "page_down"),
    # Platform-specific keys (may not exist on macOS)
    ("num_lock", "num_lock"), ("scroll_lock", "scroll_lock"),
    ("print_screen", "print_screen"), ("pause", "pause"),
    ("insert", "insert"), ("menu", "menu"),
]

PYNPUT_KEY_TO_NAME: dict[pynput_keyboard.Key, str] = {
    key: name
    for attr, name in _KEY_TO_NAME_SPEC
    if (key := _safe_key(attr)) is not None
}


# === Platform-specific key mappings (DRY: centralized for all backends) ===

# X11/xdotool key names (used by x11.py)
# xdotool uses X11 keysym names
XDOTOOL_KEY_MAP = {
    "enter": "Return",
    "tab": "Tab",
    "escape": "Escape",
    "space": "space",
    "backspace": "BackSpace",
    "delete": "Delete",
    "home": "Home",
    "end": "End",
    "page_up": "Page_Up",
    "page_down": "Page_Down",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
}


def get_xdotool_key(key_name: str) -> str:
    """Get xdotool key name for a key.

    Args:
        key_name: Key name like 'enter', 'tab'

    Returns:
        xdotool key name
    """
    return XDOTOOL_KEY_MAP.get(key_name.lower(), key_name)


# Ydotool evdev scan codes (used by wayland.py for press_key)
# These are Linux kernel scan codes
YDOTOOL_KEY_MAP = {
    "enter": "28",
    "tab": "15",
    "escape": "1",
    "space": "57",
    "backspace": "14",
    "delete": "111",
    "home": "102",
    "end": "107",
    "page_up": "104",
    "page_down": "109",
    "up": "103",
    "down": "108",
    "left": "105",
    "right": "106",
}


def get_ydotool_keycode(key_name: str) -> str | None:
    """Get ydotool keycode for a key.

    Args:
        key_name: Key name like 'enter', 'tab'

    Returns:
        ydotool keycode string or None if not found
    """
    return YDOTOOL_KEY_MAP.get(key_name.lower())


# Evdev key codes for hotkey listening (used by wayland.py)
# Lazy import to avoid dependency on non-Linux platforms
_EVDEV_KEY_MAP: dict[str, int] | None = None


def _init_evdev_map() -> dict[str, int]:
    """Initialize evdev key map (lazy loaded)."""
    global _EVDEV_KEY_MAP
    if _EVDEV_KEY_MAP is not None:
        return _EVDEV_KEY_MAP

    try:
        from evdev import ecodes

        _EVDEV_KEY_MAP = {
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
    except ImportError:
        _EVDEV_KEY_MAP = {}

    return _EVDEV_KEY_MAP


def get_evdev_keycode(key_name: str) -> int:
    """Get evdev keycode for a key name.

    Args:
        key_name: Key name like 'ctrl_r', 'f12'

    Returns:
        evdev keycode, defaults to KEY_F12 if not found
    """
    key_map = _init_evdev_map()
    key_name = key_name.lower()

    if key_name in key_map:
        return key_map[key_name]

    # Single character - try to get from ecodes
    if len(key_name) == 1:
        try:
            from evdev import ecodes

            code_name = f"KEY_{key_name.upper()}"
            return getattr(ecodes, code_name, ecodes.KEY_F12)
        except ImportError:
            pass

    # Default fallback
    try:
        from evdev import ecodes

        return ecodes.KEY_F12
    except ImportError:
        return 87  # F12 raw code
