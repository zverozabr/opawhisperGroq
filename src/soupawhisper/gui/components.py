"""Reusable GUI components."""

from typing import Any, Callable, Optional

import flet as ft


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
            on_save: Callback when value is confirmed, receives new value
            get_value: Optional function to get value from field (default: field.value)
            set_value: Optional function to set value on field (default: field.value = v)
        """
        super().__init__()
        self.field = field
        self._initial_value = initial_value
        self._current_value = initial_value
        self.on_save = on_save
        self._get_value = get_value or (lambda f: f.value)
        self._set_value = set_value or (lambda f, v: setattr(f, "value", v))

        # Confirm button - initially disabled
        self.confirm_btn = ft.IconButton(
            icon=ft.Icons.CHECK,
            icon_color=ft.Colors.GREY_500,
            disabled=True,
            tooltip="Save",
            on_click=self._on_confirm,
        )

        # Set up change detection on the field
        self._setup_change_handler()

        # Layout
        self.spacing = 4
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.controls = [
            ft.Container(content=self.field, expand=True),
            self.confirm_btn,
        ]

    def _setup_change_handler(self) -> None:
        """Set up change detection based on field type."""
        if isinstance(self.field, ft.TextField):
            self.field.on_change = self._on_field_change
        elif isinstance(self.field, ft.Dropdown):
            self.field.on_change = self._on_field_change
        elif isinstance(self.field, ft.Switch):
            self.field.on_change = self._on_field_change

    def _on_field_change(self, e: ft.ControlEvent) -> None:
        """Handle field value change."""
        new_value = self._get_value(self.field)
        is_modified = new_value != self._initial_value

        # Update button state
        self.confirm_btn.disabled = not is_modified
        self.confirm_btn.icon_color = (
            ft.Colors.GREEN_500 if is_modified else ft.Colors.GREY_500
        )

        try:
            if self.page:
                self.confirm_btn.update()
        except RuntimeError:
            pass  # Control not attached to page yet

    def _on_confirm(self, e: ft.ControlEvent) -> None:
        """Handle confirm button click."""
        new_value = self._get_value(self.field)

        # Call save callback
        self.on_save(new_value)

        # Update state - value is now saved
        self._initial_value = new_value
        self.confirm_btn.disabled = True
        self.confirm_btn.icon_color = ft.Colors.GREY_500

        try:
            if self.page:
                self.confirm_btn.update()
        except RuntimeError:
            pass  # Control not attached to page yet

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
        """Reset field to new value (e.g., after external config reload)."""
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


# Predefined hotkey display names
HOTKEY_DISPLAY_NAMES = {
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


# Virtual keyboard layout - realistic keyboard positions
# (key_name, display_label, width_multiplier)
KEYBOARD_LAYOUT: list[list[tuple[str, str, float]]] = [
    # Row 1: Function keys (Esc wider, F10-F12 slightly wider for 3 chars)
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
    # Row 6: Bottom row - modifiers and space (like real keyboard)
    [("ctrl_l", "LCtrl", 1.4), ("super_l", "LSuper", 1.5), ("alt_l", "LAlt", 1.3),
     ("space", "Space", 3),
     ("alt_r", "RAlt", 1.3), ("super_r", "RSuper", 1.5), ("ctrl_r", "RCtrl", 1.4)],
    # Row 7: Special keys
    [("tab", "Tab", 1), ("enter", "Enter", 1.3), ("backspace", "Bksp", 1.2),
     ("pause", "Pause", 1.2), ("scroll_lock", "ScrLk", 1.2), ("num_lock", "NumLk", 1.4),
     ("print_screen", "PrtSc", 1.2), ("caps_lock", "Caps", 1.2)],
]

# Keys that are letters/numbers (need modifier to be selectable)
LETTER_KEYS = set("qwertyuiopasdfghjklzxcvbnm1234567890")

# Modifier keys (including left/right variants)
MODIFIER_KEYS = {
    "ctrl", "ctrl_l", "ctrl_r",
    "alt", "alt_l", "alt_r",
    "shift", "shift_l", "shift_r",
    "super", "super_l", "super_r",
}


def parse_hotkey(hotkey: str) -> tuple[str | None, str | None]:
    """Parse hotkey string into modifier and key.

    Args:
        hotkey: Hotkey like 'f9', 'ctrl+g', 'ctrl_r'

    Returns:
        (modifier, key) tuple. For modifier-only, returns (modifier, None).
    """
    if "+" in hotkey:
        parts = hotkey.split("+", 1)
        return parts[0], parts[1]
    # If it's a modifier key alone, treat it as modifier with no key
    if hotkey in MODIFIER_KEYS:
        return hotkey, None
    return None, hotkey


def format_hotkey(modifier: str | None, key: str | None) -> str | None:
    """Format modifier and key into hotkey string.

    Args:
        modifier: Modifier like 'ctrl' or None
        key: Key like 'g', 'f9'

    Returns:
        Hotkey string like 'ctrl+g' or 'f9', or None if no key
    """
    if key is None:
        return None
    if modifier:
        return f"{modifier}+{key}"
    return key


def format_hotkey_display(hotkey: str | None) -> str:
    """Format hotkey for display."""
    if hotkey is None:
        return "Not set"
    if "+" in hotkey:
        mod, key = hotkey.split("+", 1)
        mod_display = HOTKEY_DISPLAY_NAMES.get(mod, mod.title())
        key_display = HOTKEY_DISPLAY_NAMES.get(key, key.upper())
        return f"{mod_display} + {key_display}"
    return HOTKEY_DISPLAY_NAMES.get(hotkey, hotkey.replace("_", " ").title())


class VirtualKeyboard(ft.Column):
    """Clickable virtual keyboard for hotkey selection.

    Supports:
    - Single keys: F9, Escape, etc.
    - Combos: Ctrl+G, Alt+F9, etc.

    Letters are disabled until a modifier is selected.
    """

    def __init__(
        self,
        initial_value: str | None,
        on_change: Callable[[str | None], None],
    ):
        """Initialize virtual keyboard.

        Args:
            initial_value: Initial hotkey like 'f9' or 'ctrl+g'
            on_change: Callback when selection changes
        """
        super().__init__()
        self._on_change = on_change
        self._buttons: dict[str, ft.OutlinedButton] = {}

        # Parse initial value
        self._modifier: str | None = None
        self._key: str | None = None
        if initial_value:
            self._modifier, self._key = parse_hotkey(initial_value)
            # If it's a single modifier like ctrl_r, treat as key
            if self._modifier is None and initial_value not in MODIFIER_KEYS:
                self._key = initial_value

        self._build()

    def _build(self) -> None:
        """Build keyboard UI."""
        self.spacing = 2
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        base_width = 58  # Button width for single-char keys
        base_height = 36

        for row in KEYBOARD_LAYOUT:
            row_controls = []
            for key_name, display, width_mult in row:
                is_letter = key_name in LETTER_KEYS
                is_modifier = key_name in MODIFIER_KEYS
                is_selected = self._is_selected(key_name)

                # Calculate font size based on text length and button width
                if len(display) <= 1:
                    text_size = 12
                elif len(display) <= 2:
                    text_size = 11
                elif len(display) <= 3:
                    text_size = 10
                elif len(display) <= 4:
                    text_size = 9
                else:
                    text_size = 8

                btn = ft.OutlinedButton(
                    content=ft.Text(display, size=text_size, no_wrap=True),
                    width=int(base_width * width_mult),
                    height=base_height,
                    disabled=is_letter and self._modifier is None,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PRIMARY if is_selected else None,
                        color=ft.Colors.ON_PRIMARY if is_selected else None,
                        padding=ft.Padding.symmetric(horizontal=2, vertical=2),
                    ),
                    on_click=lambda e, k=key_name: self._on_key_click(k),
                )
                self._buttons[key_name] = btn
                row_controls.append(btn)

            self.controls.append(
                ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            )

    def _is_selected(self, key_name: str) -> bool:
        """Check if key is currently selected."""
        if key_name in MODIFIER_KEYS:
            return self._modifier == key_name
        return self._key == key_name

    def _on_key_click(self, key_name: str) -> None:
        """Handle key button click."""
        if key_name in MODIFIER_KEYS:
            # Toggle modifier - don't clear key (user can see incomplete combo)
            if self._modifier == key_name:
                self._modifier = None
            else:
                self._modifier = key_name
        else:
            # Toggle key
            if self._key == key_name:
                self._key = None
            else:
                self._key = key_name

        self._update_buttons()
        self._on_change(self.selected)

    def clear(self) -> None:
        """Clear all selection."""
        self._modifier = None
        self._key = None
        self._update_buttons()
        self._on_change(None)
        # Update UI
        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass

    def _update_buttons(self) -> None:
        """Update button states after selection change."""
        for key_name, btn in self._buttons.items():
            is_letter = key_name in LETTER_KEYS
            is_selected = self._is_selected(key_name)

            # Letters disabled without modifier
            btn.disabled = is_letter and self._modifier is None

            # Update style for selection
            btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY if is_selected else None,
                color=ft.Colors.ON_PRIMARY if is_selected else None,
                padding=ft.Padding.all(4),
            )

    @property
    def selected(self) -> str | None:
        """Get current selected hotkey string.
        
        Returns None only if nothing is selected or if a letter is selected
        without a modifier. Modifier-only selections are shown but not saveable.
        """
        if self._modifier and self._key:
            return format_hotkey(self._modifier, self._key)
        if self._key:
            # Letters need a modifier to be valid
            if self._key in LETTER_KEYS:
                return None
            return self._key
        if self._modifier:
            # Modifier alone - show it but it won't be saveable
            return self._modifier
        return None
    
    @property
    def is_valid_hotkey(self) -> bool:
        """Check if current selection is a valid saveable hotkey.
        
        Valid hotkeys:
        - Modifier + key (e.g., ctrl_l+g)
        - Single special key (e.g., f9)
        - Single modifier (e.g., alt_r) - for push-to-talk style
        """
        if self._modifier and self._key:
            return True
        if self._key and self._key not in LETTER_KEYS:
            return True
        if self._modifier:
            # Allow modifier-only for push-to-talk style hotkeys
            return True
        return False

    def select(self, key_name: str) -> None:
        """Programmatically select a key (for testing)."""
        self._on_key_click(key_name)

    def reset(self, new_value: str | None) -> None:
        """Reset to new value."""
        if new_value:
            self._modifier, self._key = parse_hotkey(new_value)
            if self._modifier is None and new_value not in MODIFIER_KEYS:
                self._key = new_value
        else:
            self._modifier = None
            self._key = None
        self._update_buttons()
    
    def set_value(self, new_value: str | None) -> None:
        """Set value without triggering on_change (used for dropdown sync)."""
        if new_value:
            self._modifier, self._key = parse_hotkey(new_value)
            if self._modifier is None and new_value not in MODIFIER_KEYS:
                self._key = new_value
        else:
            self._modifier = None
            self._key = None
        self._update_buttons()


class HotkeySelector(ft.Row):
    """Hotkey selector with Change button that opens keyboard dialog.

    Shows current hotkey and allows changing via virtual keyboard popup.
    """

    # Keyboard dialog dimensions
    KEYBOARD_DIALOG_WIDTH = 920
    KEYBOARD_DIALOG_HEIGHT = 700

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
        self._original_window_width: float | None = None

        # Display current hotkey
        self._hotkey_text = ft.Text(
            format_hotkey_display(initial_value),
            size=14,
            weight=ft.FontWeight.W_500,
        )

        # Change button
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

        # Save original window size for restoration
        self._original_window_width = self.page.window.width
        self._original_window_height = self.page.window.height

        # Selection display
        self._selection_text = ft.Text(
            f"Selected: {format_hotkey_display(self._pending_value)}",
            size=14,
            weight=ft.FontWeight.W_500,
        )

        # Virtual keyboard
        self._keyboard = VirtualKeyboard(
            initial_value=self._value,
            on_change=self._on_keyboard_change,
        )

        # Dropdown lists for alternative selection
        modifier_options = [
            ft.dropdown.Option(key="", text="(none)"),
            ft.dropdown.Option(key="ctrl_l", text="Left Ctrl"),
            ft.dropdown.Option(key="ctrl_r", text="Right Ctrl"),
            ft.dropdown.Option(key="alt_l", text="Left Alt"),
            ft.dropdown.Option(key="alt_r", text="Right Alt"),
            ft.dropdown.Option(key="super_l", text="Left Super"),
            ft.dropdown.Option(key="super_r", text="Right Super"),
        ]
        
        key_options = [ft.dropdown.Option(key="", text="(select key)")]
        # Add function keys
        for i in range(1, 13):
            key_options.append(ft.dropdown.Option(key=f"f{i}", text=f"F{i}"))
        # Add ALL special keys (matching KEYBOARD_LAYOUT)
        for key, name in [
            ("escape", "Escape"), ("space", "Space"), ("tab", "Tab"),
            ("enter", "Enter"), ("backspace", "Backspace"),
            ("insert", "Insert"), ("delete", "Delete"),
            ("home", "Home"), ("end", "End"),
            ("page_up", "Page Up"), ("page_down", "Page Down"),
            ("up", "Up ↑"), ("down", "Down ↓"), ("left", "Left ←"), ("right", "Right →"),
            ("pause", "Pause"), ("scroll_lock", "Scroll Lock"),
            ("num_lock", "Num Lock"), ("print_screen", "Print Screen"),
            ("caps_lock", "Caps Lock"),
            # Numbers
            ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
            ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("0", "0"),
            # Letters
            ("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"), ("e", "E"),
            ("f", "F"), ("g", "G"), ("h", "H"), ("i", "I"), ("j", "J"),
            ("k", "K"), ("l", "L"), ("m", "M"), ("n", "N"), ("o", "O"),
            ("p", "P"), ("q", "Q"), ("r", "R"), ("s", "S"), ("t", "T"),
            ("u", "U"), ("v", "V"), ("w", "W"), ("x", "X"), ("y", "Y"), ("z", "Z"),
        ]:
            key_options.append(ft.dropdown.Option(key=key, text=name))
        
        # Parse current value for dropdowns
        current_mod, current_key = parse_hotkey(self._value) if self._value else (None, None)
        
        # If "key" is actually a modifier (e.g., "alt_r" saved alone), move it to modifier
        if current_key and current_key in MODIFIER_KEYS:
            current_mod = current_key
            current_key = None
        
        self._modifier_dropdown = ft.Dropdown(
            label="Modifier",
            value=current_mod or "",
            options=modifier_options,
            width=150,
            on_select=self._on_dropdown_change,
        )
        self._key_dropdown = ft.Dropdown(
            label="Key",
            value=current_key or "",
            options=key_options,
            width=180,
            on_select=self._on_dropdown_change,
        )

        # Create dialog with on_dismiss handler
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Select Hotkey"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Dropdown selection row
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
                width=self.KEYBOARD_DIALOG_WIDTH - 80,  # Dialog padding
            ),
            actions=[
                ft.TextButton("Clear", on_click=self._on_clear),
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.Button("Save", on_click=self._on_save_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=self._on_dialog_dismiss,
        )

        # Expand window if needed to fit keyboard
        needs_update = False
        if self.page.window.width < self.KEYBOARD_DIALOG_WIDTH:
            self.page.window.width = self.KEYBOARD_DIALOG_WIDTH
            needs_update = True
        if self.page.window.height < self.KEYBOARD_DIALOG_HEIGHT:
            self.page.window.height = self.KEYBOARD_DIALOG_HEIGHT
            needs_update = True
        if needs_update:
            self.page.update()

        # Open dialog using page.show_dialog()
        self.page.show_dialog(self._dialog)

    def _on_keyboard_change(self, value: str | None) -> None:
        """Handle keyboard selection change - sync from keyboard to dropdowns."""
        self._pending_value = value
        # Check if it's a valid hotkey (for Save button state)
        self._is_valid = self._keyboard.is_valid_hotkey if self._keyboard else False
        
        # Sync dropdowns with keyboard state (not from value string)
        if hasattr(self, "_modifier_dropdown") and hasattr(self, "_key_dropdown"):
            # Get actual state from keyboard, not parsed from string
            mod = self._keyboard._modifier if self._keyboard else None
            key = self._keyboard._key if self._keyboard else None
            
            self._modifier_dropdown.value = mod or ""
            self._key_dropdown.value = key or ""
            try:
                if self.page:
                    self._modifier_dropdown.update()
                    self._key_dropdown.update()
            except RuntimeError:
                pass
        
        self._update_selection_text(value)
    
    def _on_dropdown_change(self, e: ft.ControlEvent) -> None:
        """Handle dropdown selection change - sync from dropdowns to keyboard."""
        mod = self._modifier_dropdown.value if hasattr(self, "_modifier_dropdown") else ""
        key = self._key_dropdown.value if hasattr(self, "_key_dropdown") else ""
        
        # Directly set keyboard internal state to match dropdowns
        if self._keyboard:
            self._keyboard._modifier = mod if mod else None
            self._keyboard._key = key if key else None
            self._keyboard._update_buttons()
            try:
                if self.page:
                    self._keyboard.update()
            except RuntimeError:
                pass
        
        # Build hotkey from dropdown values
        if mod and key:
            value = format_hotkey(mod, key)
        elif key:
            value = key
        elif mod:
            value = mod
        else:
            value = None
        
        self._pending_value = value
        
        # Check if valid - modifier alone is now valid for push-to-talk
        self._is_valid = bool(mod) or bool(key and key not in LETTER_KEYS)
        
        self._update_selection_text(value)
    
    def _update_selection_text(self, value: str | None) -> None:
        """Update the selection text display."""
        if hasattr(self, "_selection_text"):
            display = format_hotkey_display(value)
            self._selection_text.value = f"Selected: {display}"
            try:
                if self.page:
                    self._selection_text.update()
            except RuntimeError:
                pass

    def _on_clear(self, e: ft.ControlEvent) -> None:
        """Handle clear button."""
        if self._keyboard:
            self._keyboard.clear()

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Handle cancel button."""
        self._close_dialog()

    def _on_save_click(self, e: ft.ControlEvent) -> None:
        """Handle save button."""
        # Only save if it's a valid hotkey (not modifier-only)
        if self._pending_value and getattr(self, "_is_valid", False):
            self._value = self._pending_value
            self._hotkey_text.value = format_hotkey_display(self._value)
            self._on_save(self._value)
            try:
                if self.page:
                    self._hotkey_text.update()
            except RuntimeError:
                pass
        self._close_dialog()

    def _on_dialog_dismiss(self, e: ft.ControlEvent) -> None:
        """Handle dialog dismiss (clicking outside)."""
        self._restore_window_size()

    def _restore_window_size(self) -> None:
        """Restore original window size."""
        if self.page:
            needs_update = False
            if self._original_window_width is not None:
                self.page.window.width = self._original_window_width
                self._original_window_width = None
                needs_update = True
            if getattr(self, "_original_window_height", None) is not None:
                self.page.window.height = self._original_window_height
                self._original_window_height = None
                needs_update = True
            if needs_update:
                self.page.update()

    def _close_dialog(self) -> None:
        """Close the dialog and restore window size."""
        if self._dialog and self.page:
            self._dialog.open = False
            self.page.update()
            self._restore_window_size()
            self._dialog = None

    @property
    def selected(self) -> str:
        """Get current selected hotkey."""
        return self._value

    @property
    def value(self) -> str:
        """Alias for selected."""
        return self._value

    def reset(self, new_value: str) -> None:
        """Reset to new value."""
        self._value = new_value
        self._hotkey_text.value = format_hotkey_display(new_value)
