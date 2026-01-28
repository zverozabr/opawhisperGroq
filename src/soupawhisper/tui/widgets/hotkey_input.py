"""Hotkey input widget for selecting keyboard shortcuts.

Single Responsibility: Capture and display hotkey configuration.
"""

from typing import Callable, Optional

from textual.containers import Horizontal
from textual.widgets import Select


# Available modifiers and keys for hotkey selection
MODIFIER_OPTIONS = [
    ("Right Ctrl", "ctrl_r"),
    ("Left Ctrl", "ctrl_l"),
    ("Right Alt", "alt_r"),
    ("Left Alt", "alt_l"),
    ("Right Cmd/Super", "super_r"),
    ("Left Cmd/Super", "super_l"),
]

KEY_OPTIONS = [
    ("(Modifier only)", ""),
    ("F12", "f12"),
    ("F11", "f11"),
    ("F10", "f10"),
    ("F9", "f9"),
    ("Space", "space"),
]


class HotkeyInput(Horizontal):
    """Widget for selecting hotkey combination.

    Displays current hotkey and allows changing via dropdowns.
    """

    DEFAULT_CSS = """
    HotkeyInput {
        height: 3;
        width: 100%;
    }

    HotkeyInput Select {
        width: 1fr;
        margin-right: 1;
    }

    HotkeyInput .hotkey-display {
        width: 12;
        padding: 1;
        background: $surface;
        text-align: center;
    }
    """

    def __init__(
        self,
        hotkey: str = "ctrl_r",
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """Initialize hotkey input.

        Args:
            hotkey: Current hotkey string (e.g., "ctrl_r", "alt_r+f12").
            on_change: Callback when hotkey changes.
        """
        super().__init__(**kwargs)
        self._hotkey = hotkey
        self._on_change = on_change
        self._modifier = ""
        self._key = ""
        self._parse_hotkey(hotkey)

    def _parse_hotkey(self, hotkey: str) -> None:
        """Parse hotkey string into modifier and key parts."""
        # Handle empty or invalid hotkey
        if not hotkey or hotkey == "+":
            self._modifier = "ctrl_r"
            self._key = ""
            return

        if "+" in hotkey:
            parts = hotkey.split("+")
            self._modifier = parts[0] if parts[0] else "ctrl_r"
            self._key = parts[1] if len(parts) > 1 else ""
        else:
            # Check if it's a modifier or a key
            modifier_values = [m[1] for m in MODIFIER_OPTIONS]
            if hotkey in modifier_values:
                self._modifier = hotkey
                self._key = ""
            else:
                self._modifier = "ctrl_r"  # Default
                self._key = hotkey

    def compose(self):
        """Create child widgets."""
        yield Select(
            options=MODIFIER_OPTIONS,
            value=self._modifier or "ctrl_r",
            id="modifier-select",
        )
        yield Select(
            options=KEY_OPTIONS,
            value=self._key,
            id="key-select",
            allow_blank=True,
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle dropdown changes."""
        if event.select.id == "modifier-select":
            self._modifier = str(event.value) if event.value else ""
        elif event.select.id == "key-select":
            self._key = str(event.value) if event.value else ""

        self._notify_change()

    def _notify_change(self) -> None:
        """Notify parent of hotkey change."""
        if self._key:
            hotkey = f"{self._modifier}+{self._key}"
        else:
            hotkey = self._modifier

        self._hotkey = hotkey
        if self._on_change:
            self._on_change(hotkey)

    @property
    def value(self) -> str:
        """Get current hotkey value."""
        return self._hotkey
