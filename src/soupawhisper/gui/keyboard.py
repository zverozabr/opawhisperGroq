"""Virtual keyboard component for hotkey selection.

Single Responsibility: Render keyboard and handle key selection.
"""

from typing import Callable

import flet as ft

from .hotkey import (
    KEYBOARD_LAYOUT,
    LETTER_KEYS,
    MODIFIER_KEYS,
    format_hotkey,
    parse_hotkey,
)


class VirtualKeyboard(ft.Column):
    """Clickable virtual keyboard for hotkey selection.

    Supports:
    - Single keys: F9, Escape, etc.
    - Combos: Ctrl+G, Alt+F9, etc.
    - Modifier-only: Alt_R for push-to-talk

    Letters/numbers are disabled until a modifier is selected.
    """

    # Button dimensions
    BASE_WIDTH = 58
    BASE_HEIGHT = 36

    def __init__(
        self,
        initial_value: str | None = None,
        on_change: Callable[[str | None], None] | None = None,
    ):
        """Initialize virtual keyboard.

        Args:
            initial_value: Initial hotkey like 'f9' or 'ctrl+g'
            on_change: Callback when selection changes
        """
        super().__init__()
        self._on_change = on_change or (lambda x: None)
        self._buttons: dict[str, ft.OutlinedButton] = {}
        self._modifier: str | None = None
        self._key: str | None = None

        if initial_value:
            self._set_from_string(initial_value)

        self._build()

    def _set_from_string(self, value: str) -> None:
        """Set internal state from hotkey string."""
        self._modifier, self._key = parse_hotkey(value)
        if self._modifier is None and value not in MODIFIER_KEYS:
            self._key = value

    def _build(self) -> None:
        """Build keyboard UI."""
        self.spacing = 2
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        for row in KEYBOARD_LAYOUT:
            row_controls = []
            for key_name, display, width_mult in row:
                btn = self._create_button(key_name, display, width_mult)
                self._buttons[key_name] = btn
                row_controls.append(btn)

            self.controls.append(
                ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            )

    def _create_button(
        self, key_name: str, display: str, width_mult: float
    ) -> ft.OutlinedButton:
        """Create a keyboard button."""
        is_letter = key_name in LETTER_KEYS
        is_selected = self._is_selected(key_name)
        text_size = self._get_text_size(display)

        return ft.OutlinedButton(
            content=ft.Text(display, size=text_size, no_wrap=True),
            width=int(self.BASE_WIDTH * width_mult),
            height=self.BASE_HEIGHT,
            disabled=is_letter and self._modifier is None,
            style=self._get_button_style(is_selected),
            on_click=lambda e, k=key_name: self._on_key_click(k),
        )

    @staticmethod
    def _get_text_size(display: str) -> int:
        """Calculate font size based on text length."""
        length = len(display)
        if length <= 1:
            return 12
        if length <= 2:
            return 11
        if length <= 3:
            return 10
        if length <= 4:
            return 9
        return 8

    @staticmethod
    def _get_button_style(is_selected: bool) -> ft.ButtonStyle:
        """Get button style based on selection state."""
        return ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY if is_selected else None,
            color=ft.Colors.ON_PRIMARY if is_selected else None,
            padding=ft.Padding.symmetric(horizontal=2, vertical=2),
        )

    def _is_selected(self, key_name: str) -> bool:
        """Check if key is currently selected."""
        if key_name in MODIFIER_KEYS:
            return self._modifier == key_name
        return self._key == key_name

    def _on_key_click(self, key_name: str) -> None:
        """Handle key button click."""
        if key_name in MODIFIER_KEYS:
            self._modifier = None if self._modifier == key_name else key_name
        else:
            self._key = None if self._key == key_name else key_name

        self._update_buttons()
        self._on_change(self.selected)

    def _update_buttons(self) -> None:
        """Update all button states."""
        for key_name, btn in self._buttons.items():
            is_letter = key_name in LETTER_KEYS
            is_selected = self._is_selected(key_name)
            btn.disabled = is_letter and self._modifier is None
            btn.style = self._get_button_style(is_selected)

    @property
    def selected(self) -> str | None:
        """Get current selected hotkey string."""
        if self._modifier and self._key:
            return format_hotkey(self._modifier, self._key)
        if self._key and self._key not in LETTER_KEYS:
            return self._key
        if self._modifier:
            return self._modifier
        return None

    @property
    def is_valid_hotkey(self) -> bool:
        """Check if current selection is a valid saveable hotkey."""
        if self._modifier and self._key:
            return True
        if self._key and self._key not in LETTER_KEYS:
            return True
        if self._modifier:
            return True  # Modifier-only for push-to-talk
        return False

    def clear(self) -> None:
        """Clear all selection."""
        self._modifier = None
        self._key = None
        self._update_buttons()
        self._on_change(None)
        self._safe_update()

    def reset(self, new_value: str | None) -> None:
        """Reset to new value."""
        if new_value:
            self._set_from_string(new_value)
        else:
            self._modifier = None
            self._key = None
        self._update_buttons()

    def set_value(self, new_value: str | None) -> None:
        """Set value without triggering on_change."""
        self.reset(new_value)

    def select(self, key_name: str) -> None:
        """Programmatically select a key (for testing)."""
        self._on_key_click(key_name)

    def _safe_update(self) -> None:
        """Safely update the control."""
        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass
