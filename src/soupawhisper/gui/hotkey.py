"""Hotkey constants and utilities.

Single Responsibility: Only hotkey parsing, formatting, and constants.
DRY: Platform detection in one place, used by all display functions.
"""

import sys

# macOS modifier symbols (Apple standard)
_MACOS_MODIFIER_SYMBOLS: dict[str, str] = {
    "ctrl": "⌃", "ctrl_l": "⌃", "ctrl_r": "⌃",
    "alt": "⌥", "alt_l": "⌥", "alt_r": "⌥",
    "super": "⌘", "super_l": "⌘", "super_r": "⌘",
    "shift": "⇧", "shift_l": "⇧", "shift_r": "⇧",
}

# macOS modifier full names
_MACOS_MODIFIER_NAMES: dict[str, str] = {
    "ctrl": "Control", "ctrl_l": "Control", "ctrl_r": "Control",
    "alt": "Option", "alt_l": "Option", "alt_r": "Option",
    "super": "Command", "super_l": "Command", "super_r": "Command",
    "shift": "Shift", "shift_l": "Shift", "shift_r": "Shift",
}

# Default modifier names (Windows/Linux)
_DEFAULT_MODIFIER_NAMES: dict[str, str] = {
    "ctrl": "Ctrl", "ctrl_l": "Left Ctrl", "ctrl_r": "Right Ctrl",
    "alt": "Alt", "alt_l": "Left Alt", "alt_r": "Right Alt",
    "super": "Super", "super_l": "Left Super", "super_r": "Right Super",
    "shift": "Shift", "shift_l": "Left Shift", "shift_r": "Right Shift",
}


def get_modifier_display(key: str, use_symbol: bool = True) -> str:
    """Get platform-specific display name for modifier key.

    Args:
        key: Modifier key name (e.g., 'ctrl_l', 'super_r')
        use_symbol: If True, use symbol on macOS (⌘), else full name

    Returns:
        Display string for the modifier
    """
    if sys.platform == "darwin":
        if use_symbol:
            return _MACOS_MODIFIER_SYMBOLS.get(key, key)
        return _MACOS_MODIFIER_NAMES.get(key, key)
    return _DEFAULT_MODIFIER_NAMES.get(key, key)


# Predefined hotkey display names
HOTKEY_DISPLAY_NAMES: dict[str, str] = {
    # Modifiers
    "ctrl": "Ctrl", "ctrl_r": "Right Ctrl", "ctrl_l": "Left Ctrl",
    "alt": "Alt", "alt_r": "Right Alt", "alt_l": "Left Alt",
    "shift": "Shift", "shift_r": "Right Shift", "shift_l": "Left Shift",
    "super": "Super", "super_r": "Right Super", "super_l": "Left Super",
    # Function keys
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
    # Special keys
    "space": "Space", "enter": "Enter", "tab": "Tab",
    "escape": "Escape", "backspace": "Backspace", "pause": "Pause",
    "insert": "Insert", "delete": "Delete", "home": "Home", "end": "End",
    # Navigation
    "page_up": "Page Up", "page_down": "Page Down",
    "up": "↑", "down": "↓", "left": "←", "right": "→",
    # Lock keys
    "num_lock": "Num Lock", "scroll_lock": "Scroll Lock", "caps_lock": "Caps Lock",
    "print_screen": "Print Screen",
}

# Keys that require a modifier (letters/numbers)
LETTER_KEYS: set[str] = set("qwertyuiopasdfghjklzxcvbnm1234567890")

# Modifier keys (including left/right variants)
MODIFIER_KEYS: set[str] = {
    "ctrl", "ctrl_l", "ctrl_r",
    "alt", "alt_l", "alt_r",
    "shift", "shift_l", "shift_r",
    "super", "super_l", "super_r",
}

# Common keyboard rows (shared between platforms)
_COMMON_ROWS: list[list[tuple[str, str, float]]] = [
    # Row 1: Function keys
    [("escape", "Esc", 1.1), ("f1", "F1", 1), ("f2", "F2", 1), ("f3", "F3", 1), ("f4", "F4", 1),
     ("f5", "F5", 1), ("f6", "F6", 1), ("f7", "F7", 1), ("f8", "F8", 1),
     ("f9", "F9", 1), ("f10", "F10", 1.1), ("f11", "F11", 1.1), ("f12", "F12", 1.1)],
    # Row 2: Numbers
    [("1", "1", 1), ("2", "2", 1), ("3", "3", 1), ("4", "4", 1), ("5", "5", 1),
     ("6", "6", 1), ("7", "7", 1), ("8", "8", 1), ("9", "9", 1), ("0", "0", 1),
     ("insert", "Ins", 1.1), ("delete", "Del", 1.1)],
    # Row 3: QWERTY + navigation
    [("q", "Q", 1), ("w", "W", 1), ("e", "E", 1), ("r", "R", 1), ("t", "T", 1),
     ("y", "Y", 1), ("u", "U", 1), ("i", "I", 1), ("o", "O", 1), ("p", "P", 1),
     ("home", "Hom", 1.1), ("end", "End", 1.1)],
    # Row 4: ASDF + arrows
    [("a", "A", 1), ("s", "S", 1), ("d", "D", 1), ("f", "F", 1), ("g", "G", 1),
     ("h", "H", 1), ("j", "J", 1), ("k", "K", 1), ("l", "L", 1),
     ("up", "↑", 1), ("page_up", "PgU", 1.1)],
    # Row 5: ZXCV + arrows
    [("z", "Z", 1), ("x", "X", 1), ("c", "C", 1), ("v", "V", 1), ("b", "B", 1),
     ("n", "N", 1), ("m", "M", 1),
     ("left", "←", 1), ("down", "↓", 1), ("right", "→", 1), ("page_down", "PgD", 1.1)],
]

# macOS modifier row (with symbols)
_MACOS_MODIFIER_ROW: list[tuple[str, str, float]] = [
    ("ctrl_l", "⌃", 1.4), ("super_l", "⌘", 1.5), ("alt_l", "⌥", 1.3),
    ("space", "Space", 3),
    ("alt_r", "⌥", 1.3), ("super_r", "⌘", 1.5), ("ctrl_r", "⌃", 1.4),
]

# Default modifier row (Windows/Linux)
_DEFAULT_MODIFIER_ROW: list[tuple[str, str, float]] = [
    ("ctrl_l", "LCtrl", 1.4), ("super_l", "LSuper", 1.5), ("alt_l", "LAlt", 1.3),
    ("space", "Space", 3),
    ("alt_r", "RAlt", 1.3), ("super_r", "RSuper", 1.5), ("ctrl_r", "RCtrl", 1.4),
]

# Special keys row (same for all platforms)
_SPECIAL_KEYS_ROW: list[tuple[str, str, float]] = [
    ("tab", "Tab", 1), ("enter", "Enter", 1.3), ("backspace", "Bksp", 1.2),
    ("pause", "Pause", 1.2), ("scroll_lock", "ScrLk", 1.2), ("num_lock", "NumLk", 1.4),
    ("print_screen", "PrtSc", 1.2), ("caps_lock", "Caps", 1.2),
]


def get_keyboard_layout() -> list[list[tuple[str, str, float]]]:
    """Get platform-specific keyboard layout.

    Returns:
        Keyboard layout with platform-appropriate modifier labels.
    """
    modifier_row = _MACOS_MODIFIER_ROW if sys.platform == "darwin" else _DEFAULT_MODIFIER_ROW
    return [*_COMMON_ROWS, modifier_row, _SPECIAL_KEYS_ROW]


# Legacy: Keep KEYBOARD_LAYOUT for backward compatibility
# New code should use get_keyboard_layout()
KEYBOARD_LAYOUT = get_keyboard_layout()


def parse_hotkey(hotkey: str) -> tuple[str | None, str | None]:
    """Parse hotkey string into (modifier, key) tuple.

    Examples:
        'f9' -> (None, 'f9')
        'ctrl+g' -> ('ctrl', 'g')
        'alt_r' -> ('alt_r', None)  # modifier-only
    """
    if "+" in hotkey:
        parts = hotkey.split("+", 1)
        return parts[0], parts[1]
    if hotkey in MODIFIER_KEYS:
        return hotkey, None
    return None, hotkey


def format_hotkey(modifier: str | None, key: str | None) -> str | None:
    """Format modifier and key into hotkey string.

    Examples:
        ('ctrl', 'g') -> 'ctrl+g'
        (None, 'f9') -> 'f9'
        ('alt_r', None) -> None  # modifier-only not valid for save
    """
    if key is None:
        return None
    if modifier:
        return f"{modifier}+{key}"
    return key


def format_hotkey_display(hotkey: str | None) -> str:
    """Format hotkey for user-friendly display (platform-aware).

    On macOS uses Command/Option/Control names.
    On Windows/Linux uses Ctrl/Alt/Super names.

    Examples:
        'ctrl+g' -> 'Ctrl + G' (Linux) or 'Control + G' (macOS)
        'super_r' -> 'Right Super' (Linux) or 'Command' (macOS)
        'f9' -> 'F9'
        None -> 'Not set'
    """
    if hotkey is None:
        return "Not set"

    if "+" in hotkey:
        mod, key = hotkey.split("+", 1)
        mod_display = get_modifier_display(mod, use_symbol=False)
        key_display = HOTKEY_DISPLAY_NAMES.get(key, key.upper())
        return f"{mod_display} + {key_display}"

    # Single key - check if it's a modifier
    if hotkey in MODIFIER_KEYS:
        return get_modifier_display(hotkey, use_symbol=False)

    return HOTKEY_DISPLAY_NAMES.get(hotkey, hotkey.replace("_", " ").title())
