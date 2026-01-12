"""Reusable GUI components.

This module provides generic UI components and re-exports hotkey components
for backwards compatibility.

SOLID principles applied:
- Single Responsibility: Each component has one job
- Open/Closed: Components extensible without modification
- DRY: Common patterns extracted to base classes
- KISS: Simple, focused implementations
"""

from typing import Any, Callable, Optional

import flet as ft

# Re-export hotkey components for backwards compatibility
from .hotkey import (
    HOTKEY_DISPLAY_NAMES,
    KEYBOARD_LAYOUT,
    LETTER_KEYS,
    MODIFIER_KEYS,
    format_hotkey,
    format_hotkey_display,
    parse_hotkey,
)
from .hotkey_selector import HotkeySelector
from .keyboard import VirtualKeyboard

__all__ = [
    # Generic components
    "EditableField",
    "SettingsSection",
    # Hotkey components (re-exported)
    "VirtualKeyboard",
    "HotkeySelector",
    # Hotkey utilities (re-exported)
    "HOTKEY_DISPLAY_NAMES",
    "KEYBOARD_LAYOUT",
    "LETTER_KEYS",
    "MODIFIER_KEYS",
    "parse_hotkey",
    "format_hotkey",
    "format_hotkey_display",
]


class EditableField(ft.Row):
    """Field with inline confirm button that appears on edit.

    The confirm button is disabled until the field value changes.
    After confirming, the button becomes gray until next edit.
    """

    def __init__(
        self,
        field: ft.Control,
        initial_value: Any,
        on_save: Callable[[Any], None],
        get_value: Optional[Callable[[ft.Control], Any]] = None,
        set_value: Optional[Callable[[ft.Control, Any], None]] = None,
    ):
        """Initialize editable field.

        Args:
            field: The input control (TextField, Dropdown, Switch, etc.)
            initial_value: Initial value to track changes against
            on_save: Callback when value is confirmed
            get_value: Optional function to get value from field
            set_value: Optional function to set value on field
        """
        super().__init__()
        self.field = field
        self._initial_value = initial_value
        self._current_value = initial_value
        self.on_save = on_save
        self._get_value = get_value or (lambda f: f.value)
        self._set_value = set_value or (lambda f, v: setattr(f, "value", v))

        self.confirm_btn = ft.IconButton(
            icon=ft.Icons.CHECK,
            icon_color=ft.Colors.GREY_500,
            disabled=True,
            tooltip="Save",
            on_click=self._on_confirm,
        )

        self._setup_change_handler()

        self.spacing = 4
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.controls = [
            ft.Container(content=self.field, expand=True),
            self.confirm_btn,
        ]

    def _setup_change_handler(self) -> None:
        """Set up change detection based on field type."""
        if isinstance(self.field, (ft.TextField, ft.Dropdown, ft.Switch)):
            self.field.on_change = self._on_field_change

    def _on_field_change(self, e: ft.ControlEvent) -> None:
        """Handle field value change."""
        new_value = self._get_value(self.field)
        is_modified = new_value != self._initial_value

        self.confirm_btn.disabled = not is_modified
        self.confirm_btn.icon_color = (
            ft.Colors.GREEN_500 if is_modified else ft.Colors.GREY_500
        )
        self._safe_update(self.confirm_btn)

    def _on_confirm(self, e: ft.ControlEvent) -> None:
        """Handle confirm button click."""
        new_value = self._get_value(self.field)
        self.on_save(new_value)

        self._initial_value = new_value
        self.confirm_btn.disabled = True
        self.confirm_btn.icon_color = ft.Colors.GREY_500
        self._safe_update(self.confirm_btn)

    def _safe_update(self, control: ft.Control) -> None:
        """Safely update a control."""
        try:
            if self.page:
                control.update()
        except RuntimeError:
            pass

    @property
    def value(self) -> Any:
        """Get current field value."""
        return self._get_value(self.field)

    @value.setter
    def value(self, v: Any) -> None:
        """Set field value."""
        self._set_value(self.field, v)
        self._initial_value = v

    def reset(self, new_value: Any) -> None:
        """Reset field to new value."""
        self._set_value(self.field, new_value)
        self._initial_value = new_value
        self.confirm_btn.disabled = True
        self.confirm_btn.icon_color = ft.Colors.GREY_500


class SettingsSection(ft.Column):
    """A section of settings with a header."""

    def __init__(self, title: str, controls: list[ft.Control]):
        """Initialize settings section.

        Args:
            title: Section title
            controls: List of controls in this section
        """
        super().__init__()
        self.spacing = 8
        self.controls = [
            ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
            *controls,
        ]
