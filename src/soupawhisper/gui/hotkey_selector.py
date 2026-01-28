"""Hotkey selector component with dialog.

Single Responsibility: Manage hotkey selection dialog and state.
"""

import sys
from typing import Callable

import flet as ft

from .base import get_page_safe, safe_update
from .hotkey import (
    MODIFIER_KEYS,
    format_hotkey,
    format_hotkey_display,
    get_modifier_display,
    parse_hotkey,
)
from .keyboard import VirtualKeyboard


def _build_modifier_options() -> list[ft.dropdown.Option]:
    """Build platform-specific modifier dropdown options.

    On macOS uses Command/Option/Control with symbols.
    On Windows/Linux uses Ctrl/Alt/Super.
    """
    if sys.platform == "darwin":
        return [
            ft.dropdown.Option(key="", text="(none)"),
            ft.dropdown.Option(key="ctrl_l", text="⌃ Control"),
            ft.dropdown.Option(key="super_l", text="⌘ Command"),
            ft.dropdown.Option(key="super_r", text="⌘ Command (Right)"),
            ft.dropdown.Option(key="alt_l", text="⌥ Option"),
            ft.dropdown.Option(key="alt_r", text="⌥ Option (Right)"),
        ]
    return [
        ft.dropdown.Option(key="", text="(none)"),
        ft.dropdown.Option(key="ctrl_l", text="Left Ctrl"),
        ft.dropdown.Option(key="ctrl_r", text="Right Ctrl"),
        ft.dropdown.Option(key="alt_l", text="Left Alt"),
        ft.dropdown.Option(key="alt_r", text="Right Alt"),
        ft.dropdown.Option(key="super_l", text="Left Super"),
        ft.dropdown.Option(key="super_r", text="Right Super"),
    ]


# Build options at import time for current platform
MODIFIER_OPTIONS = _build_modifier_options()


def _build_key_options() -> list[ft.dropdown.Option]:
    """Build key dropdown options."""
    options = [ft.dropdown.Option(key="", text="(select key)")]

    # Function keys
    for i in range(1, 13):
        options.append(ft.dropdown.Option(key=f"f{i}", text=f"F{i}"))

    # Special keys
    special_keys = [
        ("escape", "Escape"), ("space", "Space"), ("tab", "Tab"),
        ("enter", "Enter"), ("backspace", "Backspace"),
        ("insert", "Insert"), ("delete", "Delete"),
        ("home", "Home"), ("end", "End"),
        ("page_up", "Page Up"), ("page_down", "Page Down"),
        ("up", "Up ↑"), ("down", "Down ↓"), ("left", "Left ←"), ("right", "Right →"),
        ("pause", "Pause"), ("scroll_lock", "Scroll Lock"),
        ("num_lock", "Num Lock"), ("print_screen", "Print Screen"),
        ("caps_lock", "Caps Lock"),
    ]

    # Numbers
    for n in "1234567890":
        special_keys.append((n, n))

    # Letters
    for c in "abcdefghijklmnopqrstuvwxyz":
        special_keys.append((c, c.upper()))

    for key, name in special_keys:
        options.append(ft.dropdown.Option(key=key, text=name))

    return options


class HotkeySelector(ft.Row):
    """Hotkey selector with Change button that opens keyboard dialog."""

    DIALOG_WIDTH = 920
    DIALOG_HEIGHT = 700

    def __init__(
        self,
        initial_value: str,
        on_save: Callable[[str], None],
    ):
        """Initialize hotkey selector.

        Args:
            initial_value: Current hotkey value
            on_save: Callback when new hotkey is saved
        """
        super().__init__()
        self._value = initial_value
        self._on_save = on_save
        self._pending_value: str | None = None
        self._dialog: ft.AlertDialog | None = None
        self._keyboard: VirtualKeyboard | None = None
        self._original_size: tuple[float, float] | None = None

        # UI components
        self._hotkey_text = ft.Text(
            format_hotkey_display(initial_value),
            size=14,
            weight=ft.FontWeight.W_500,
        )
        self._change_btn = ft.Button(
            content=ft.Text("Change"),
            on_click=self._open_dialog,
        )

        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 12
        self.controls = [
            ft.Text("Hotkey:", size=14),
            self._hotkey_text,
            self._change_btn,
        ]

    def _open_dialog(self, e: ft.ControlEvent) -> None:
        """Open keyboard dialog."""
        if not self.page:
            return

        self._pending_value = self._value
        self._original_size = (self.page.window.width, self.page.window.height)

        # Parse current value for dropdowns
        current_mod, current_key = self._parse_current_value()

        # Create components
        self._selection_text = ft.Text(
            f"Selected: {format_hotkey_display(self._pending_value)}",
            size=14,
            weight=ft.FontWeight.W_500,
        )

        self._keyboard = VirtualKeyboard(
            initial_value=self._value,
            on_change=self._on_keyboard_change,
        )

        self._modifier_dropdown = ft.Dropdown(
            label="Modifier",
            value=current_mod or "",
            options=MODIFIER_OPTIONS,
            width=150,
            on_select=self._on_dropdown_change,
        )

        self._key_dropdown = ft.Dropdown(
            label="Key",
            value=current_key or "",
            options=_build_key_options(),
            width=180,
            on_select=self._on_dropdown_change,
        )

        # Build dialog
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Select Hotkey"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            self._modifier_dropdown,
                            ft.Text("+", size=16),
                            self._key_dropdown,
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(),
                        ft.Text("Or click buttons:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        self._keyboard,
                        ft.Divider(),
                        self._selection_text,
                    ],
                    tight=True,
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=self.DIALOG_WIDTH - 80,
            ),
            actions=[
                ft.TextButton("Clear", on_click=self._on_clear),
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.Button("Save", on_click=self._on_save_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=self._on_dialog_dismiss,
        )

        # Resize window if needed
        self._expand_window()

        # Add keyboard event handler for physical key capture
        self._old_keyboard_handler = self.page.on_keyboard_event
        self.page.on_keyboard_event = self._on_physical_key

        self.page.show_dialog(self._dialog)

    def _parse_current_value(self) -> tuple[str | None, str | None]:
        """Parse current value for dropdown initialization."""
        if not self._value:
            return None, None

        mod, key = parse_hotkey(self._value)
        # If key is a modifier (saved modifier-only), treat as modifier
        if key and key in MODIFIER_KEYS:
            return key, None
        return mod, key

    def _expand_window(self) -> None:
        """Expand window to fit dialog if needed."""
        if not self.page:
            return

        needs_update = False
        if self.page.window.width < self.DIALOG_WIDTH:
            self.page.window.width = self.DIALOG_WIDTH
            needs_update = True
        if self.page.window.height < self.DIALOG_HEIGHT:
            self.page.window.height = self.DIALOG_HEIGHT
            needs_update = True
        if needs_update:
            self.page.update()

    def _on_physical_key(self, e: ft.KeyboardEvent) -> None:
        """Handle physical keyboard input when dialog is open.

        Uses handle_physical_key_with_modifiers to work around Flutter bug #148936
        on macOS where Right Control doesn't return a key name.
        """
        if self._keyboard and self._dialog and self._dialog.open:
            # Use method with modifier flags for macOS Right Control workaround
            self._keyboard.handle_physical_key_with_modifiers(
                key=e.key,
                ctrl=e.ctrl,
                alt=e.alt,
                shift=e.shift,
                meta=e.meta,
            )
            self._safe_update(self._keyboard)

    def _on_keyboard_change(self, value: str | None) -> None:
        """Sync dropdowns from keyboard."""
        self._pending_value = value

        if self._keyboard and self._modifier_dropdown and self._key_dropdown:
            self._modifier_dropdown.value = self._keyboard._modifier or ""
            self._key_dropdown.value = self._keyboard._key or ""
            self._safe_update(self._modifier_dropdown)
            self._safe_update(self._key_dropdown)

        self._update_selection_text(value)

    def _on_dropdown_change(self, e: ft.ControlEvent) -> None:
        """Sync keyboard from dropdowns."""
        mod = self._modifier_dropdown.value if self._modifier_dropdown else ""
        key = self._key_dropdown.value if self._key_dropdown else ""

        # Update keyboard state
        if self._keyboard:
            self._keyboard._modifier = mod or None
            self._keyboard._key = key or None
            self._keyboard._update_buttons()
            self._safe_update(self._keyboard)

        # Build hotkey string
        value = self._build_hotkey(mod, key)
        self._pending_value = value
        self._update_selection_text(value)

    def _build_hotkey(self, mod: str, key: str) -> str | None:
        """Build hotkey string from mod and key."""
        if mod and key:
            return format_hotkey(mod, key)
        if key:
            return key
        if mod:
            return mod
        return None

    def _update_selection_text(self, value: str | None) -> None:
        """Update selection display."""
        if hasattr(self, "_selection_text") and self._selection_text:
            self._selection_text.value = f"Selected: {format_hotkey_display(value)}"
            self._safe_update(self._selection_text)

    def _on_clear(self, e: ft.ControlEvent) -> None:
        """Handle clear button."""
        if self._keyboard:
            self._keyboard.clear()

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Handle cancel button."""
        self._close_dialog()

    def _on_save_click(self, e: ft.ControlEvent) -> None:
        """Handle save button."""
        is_valid = self._keyboard.is_valid_hotkey if self._keyboard else False

        if self._pending_value and is_valid:
            self._value = self._pending_value
            self._hotkey_text.value = format_hotkey_display(self._value)
            self._on_save(self._value)
            self._safe_update(self._hotkey_text)

        self._close_dialog()

    def _on_dialog_dismiss(self, e: ft.ControlEvent) -> None:
        """Handle dialog dismiss."""
        self._restore_window()

    def _close_dialog(self) -> None:
        """Close dialog and restore window."""
        if self._dialog and self.page:
            # Restore old keyboard handler
            if hasattr(self, "_old_keyboard_handler"):
                self.page.on_keyboard_event = self._old_keyboard_handler

            self._dialog.open = False
            self.page.update()
            self._restore_window()
            self._dialog = None

    def _restore_window(self) -> None:
        """Restore original window size."""
        if self.page and self._original_size:
            w, h = self._original_size
            self.page.window.width = w
            self.page.window.height = h
            self.page.update()
            self._original_size = None

    def _safe_update(self, control: ft.Control) -> None:
        """Safely update a control."""
        page = get_page_safe(self)
        safe_update(page, control)

    @property
    def value(self) -> str:
        """Get current selected hotkey."""
        return self._value

    @property
    def selected(self) -> str:
        """Alias for value."""
        return self._value

    def reset(self, new_value: str) -> None:
        """Reset to new value."""
        self._value = new_value
        self._hotkey_text.value = format_hotkey_display(new_value)
