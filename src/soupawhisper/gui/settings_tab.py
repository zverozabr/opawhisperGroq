"""Settings tab component with inline field saving."""

import sys
from typing import Callable

import flet as ft

from soupawhisper.audio import AudioRecorder
from soupawhisper.config import Config

from .base import show_snack_on_control
from .components import EditableField, HotkeySelector, SettingsSection


# Language options
LANGUAGES = [
    ("auto", "Auto"),
    ("ru", "Russian"),
    ("en", "English"),
    ("de", "German"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
]

# Whisper model options
MODELS = [
    ("whisper-large-v3", "Whisper Large V3 (best)"),
    ("whisper-large-v3-turbo", "Whisper Large V3 Turbo (fast)"),
    ("distil-whisper-large-v3-en", "Distil Whisper (English only)"),
]

# Backend options
BACKENDS = [
    ("auto", "Auto-detect"),
    ("x11", "X11"),
    ("wayland", "Wayland"),
    ("darwin", "macOS"),
    ("windows", "Windows"),
]


class SettingsTab(ft.Column):
    """Tab for editing application settings with inline save."""

    def __init__(self, config: Config, on_save: Callable[[str, object], None]):
        """Initialize settings tab.

        Args:
            config: Current configuration
            on_save: Callback when a field is saved, receives (field_name, new_value)
        """
        super().__init__()
        self.config = config
        self.on_save = on_save
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

    def build(self) -> ft.Column:
        """Build settings form with editable fields."""
        # API Key field
        api_key_field = ft.TextField(
            label="Groq API Key",
            value=self.config.api_key,
            password=True,
            can_reveal_password=True,
            hint_text="gsk_...",
        )
        self.api_key_editable = EditableField(
            field=api_key_field,
            initial_value=self.config.api_key,
            on_save=lambda v: self._save_field("api_key", v),
        )

        # Model dropdown
        model_dropdown = ft.Dropdown(
            label="Whisper Model",
            value=self.config.model,
            options=[ft.dropdown.Option(key=k, text=v) for k, v in MODELS],
        )
        self.model_editable = EditableField(
            field=model_dropdown,
            initial_value=self.config.model,
            on_save=lambda v: self._save_field("model", v),
        )

        # Language dropdown
        language_dropdown = ft.Dropdown(
            label="Recognition Language",
            value=self.config.language,
            options=[ft.dropdown.Option(key=k, text=v) for k, v in LANGUAGES],
        )
        self.language_editable = EditableField(
            field=language_dropdown,
            initial_value=self.config.language,
            on_save=lambda v: self._save_field("language", v),
        )

        # Hotkey selector with dialog
        self.hotkey_selector = HotkeySelector(
            initial_value=self.config.hotkey,
            on_save=lambda v: self._save_field("hotkey", v),
        )

        # Audio device dropdown (refreshes on focus to detect newly connected devices)
        devices = self._get_audio_devices()
        device_dropdown = ft.Dropdown(
            label="Microphone",
            value=self.config.audio_device,
            options=[ft.dropdown.Option(key=d[0], text=d[1]) for d in devices],
            on_focus=self._refresh_audio_devices,
        )
        self.device_editable = EditableField(
            field=device_dropdown,
            initial_value=self.config.audio_device,
            on_save=lambda v: self._save_field("audio_device", v),
        )

        # Auto-type switch
        auto_type_switch = ft.Switch(
            label="Auto-type text",
            value=self.config.auto_type,
        )
        self.auto_type_editable = EditableField(
            field=auto_type_switch,
            initial_value=self.config.auto_type,
            on_save=lambda v: self._save_field("auto_type", v),
        )

        # Auto-enter switch
        auto_enter_switch = ft.Switch(
            label="Press Enter after",
            value=self.config.auto_enter,
        )
        self.auto_enter_editable = EditableField(
            field=auto_enter_switch,
            initial_value=self.config.auto_enter,
            on_save=lambda v: self._save_field("auto_enter", v),
        )

        # Typing delay field
        typing_delay_field = ft.TextField(
            label="Typing delay (ms)",
            value=str(self.config.typing_delay),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
        )
        self.typing_delay_editable = EditableField(
            field=typing_delay_field,
            initial_value=str(self.config.typing_delay),
            on_save=lambda v: self._save_field("typing_delay", self._parse_int(v, 12)),
        )

        # History enabled switch
        history_enabled_switch = ft.Switch(
            label="Save history",
            value=self.config.history_enabled,
        )
        self.history_enabled_editable = EditableField(
            field=history_enabled_switch,
            initial_value=self.config.history_enabled,
            on_save=lambda v: self._save_field("history_enabled", v),
        )

        # History days field
        history_days_field = ft.TextField(
            label="Keep days",
            value=str(self.config.history_days),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
        )
        self.history_days_editable = EditableField(
            field=history_days_field,
            initial_value=str(self.config.history_days),
            on_save=lambda v: self._save_field("history_days", max(1, self._parse_int(v, 3))),
        )

        # Notifications switch
        notifications_switch = ft.Switch(
            label="Show notifications",
            value=self.config.notifications,
        )
        self.notifications_editable = EditableField(
            field=notifications_switch,
            initial_value=self.config.notifications,
            on_save=lambda v: self._save_field("notifications", v),
        )

        # Backend dropdown
        backend_dropdown = ft.Dropdown(
            label="Display Backend",
            value=self.config.backend,
            options=[ft.dropdown.Option(key=k, text=v) for k, v in BACKENDS],
        )
        self.backend_editable = EditableField(
            field=backend_dropdown,
            initial_value=self.config.backend,
            on_save=lambda v: self._save_field("backend", v),
        )

        # Debug switch
        debug_switch = ft.Switch(
            label="Debug mode",
            value=self.config.debug,
        )
        self.debug_editable = EditableField(
            field=debug_switch,
            initial_value=self.config.debug,
            on_save=lambda v: self._save_field("debug", v),
        )

        # Build layout
        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        SettingsSection("API", [
                            self.api_key_editable,
                            self.model_editable,
                        ]),
                        ft.Divider(),
                        SettingsSection("Recognition", [
                            self.language_editable,
                            self.device_editable,
                        ]),
                        ft.Divider(),
                        SettingsSection("Hotkey", [self.hotkey_selector]),
                        ft.Divider(),
                        SettingsSection("Text Input", [
                            self.auto_type_editable,
                            self.auto_enter_editable,
                            self.typing_delay_editable,
                        ]),
                        ft.Divider(),
                        SettingsSection("History", [
                            self.history_enabled_editable,
                            self.history_days_editable,
                        ]),
                        ft.Divider(),
                        SettingsSection("System", [
                            self.notifications_editable,
                            self.backend_editable,
                            self._build_permissions_button(),
                        ]),
                        ft.Divider(),
                        SettingsSection("Developer", [self.debug_editable]),
                    ],
                    spacing=12,
                ),
                padding=16,
            )
        ]

        return self

    def _build_permissions_button(self) -> ft.Control:
        """Build macOS permissions button (only visible on macOS)."""
        if sys.platform != "darwin":
            return ft.Container()  # Empty on non-macOS

        def open_permissions(e):
            from soupawhisper.backend.darwin import (
                PermissionsHelper,
                check_accessibility,
            )
            from soupawhisper.clipboard import copy_to_clipboard

            # Get current status and Python path using PermissionsHelper (DRY)
            status = PermissionsHelper.check()
            target = PermissionsHelper.get_python_path()
            copy_to_clipboard(target)

            def request_access(ev):
                """Try to trigger system permission prompt."""
                check_accessibility(prompt=True)
                show_snack_on_control(self, "System prompt triggered (if not already granted)")

            def open_accessibility(ev):
                PermissionsHelper.open_accessibility_with_finder()

            def open_input_mon(ev):
                PermissionsHelper.open_input_monitoring_with_finder()

            def close_dlg(ev):
                dlg.open = False
                if self.page:
                    self.page.update()

            def restart_app(ev):
                """Restart the application."""
                import os
                os.execv(sys.executable, [sys.executable] + sys.argv)

            # Build status text showing current permissions
            status_color = "green" if status.all_granted else "orange"
            status_text = "All OK" if status.all_granted else f"Missing: {', '.join(status.missing)}"

            dlg = ft.AlertDialog(
                modal=False,
                title=ft.Text("macOS Permissions Setup"),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Status: ", size=12),
                        ft.Text(status_text, size=12, color=status_color, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text("Path copied to clipboard!", color="green", size=12),
                    ft.Container(
                        content=ft.Text(target, size=11, selectable=True),
                        bgcolor="#333333",
                        padding=10,
                        border_radius=4,
                    ),
                    ft.Divider(),
                    ft.Text("Steps for each:", weight=ft.FontWeight.BOLD),
                    ft.Text("1. Click '+' at bottom of list"),
                    ft.Text("2. Press Cmd+Shift+G"),
                    ft.Text("3. Paste (Cmd+V) → Go → Open"),
                    ft.Text("4. Enable toggle"),
                    ft.Divider(),
                    ft.Button(
                        "Request Access (System Prompt)",
                        icon=ft.Icons.VERIFIED_USER,
                        on_click=request_access,
                        bgcolor="blue",
                        color="white",
                    ),
                    ft.Text("If prompt doesn't add app, use buttons below:", size=11),
                    ft.Row([
                        ft.Button(
                            "1. Accessibility",
                            icon=ft.Icons.ACCESSIBILITY,
                            on_click=open_accessibility,
                        ),
                        ft.Button(
                            "2. Input Monitoring",
                            icon=ft.Icons.KEYBOARD,
                            on_click=open_input_mon,
                        ),
                    ], spacing=10),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("After adding to BOTH →", color="orange"),
                        ft.Button(
                            "Restart App",
                            icon=ft.Icons.REFRESH,
                            on_click=restart_app,
                            bgcolor="orange",
                            color="white",
                        ),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ], tight=True, spacing=8, width=420),
                actions=[ft.TextButton("Close", on_click=close_dlg)],
            )

            # Expand window to not overlap
            if self.page:
                if self.page.window.width < 500:
                    self.page.window.width = 500
                if self.page.window.height < 600:
                    self.page.window.height = 600
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()

        return ft.Container(
            content=ft.Button(
                "Setup macOS Permissions",
                icon=ft.Icons.SECURITY,
                on_click=open_permissions,
            ),
            padding=ft.Padding.only(top=8),
        )

    def _get_audio_devices(self) -> list[tuple[str, str]]:
        """Get list of available audio devices."""
        devices = [("default", "Default")]
        try:
            for device in AudioRecorder.list_devices():
                devices.append((device.id, device.name))
        except Exception:
            pass
        return devices

    def _refresh_audio_devices(self, e) -> None:
        """Refresh device list when dropdown receives focus.

        This detects newly connected devices (e.g., Bluetooth microphones)
        without requiring app restart.
        """
        devices = self._get_audio_devices()
        dropdown = self.device_editable.field
        current_value = dropdown.value

        # Update options
        dropdown.options = [ft.dropdown.Option(key=d[0], text=d[1]) for d in devices]

        # Keep current value if still valid, otherwise reset to default
        valid_ids = {d[0] for d in devices}
        if current_value not in valid_ids:
            dropdown.value = "default"

        # Update UI
        if self.page:
            dropdown.update()

    def _parse_int(self, value: str, default: int) -> int:
        """Parse integer from string with fallback."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _save_field(self, field_name: str, value: object) -> None:
        """Save a single field value."""
        # Update local config
        setattr(self.config, field_name, value)
        # Notify parent to save
        self.on_save(field_name, value)

        # Show confirmation
        self._show_saved_notification(field_name)

    def _show_saved_notification(self, field_name: str) -> None:
        """Show brief save confirmation."""
        show_snack_on_control(self, "Saved")

    def update_config(self, new_config: Config) -> None:
        """Update all fields from new config (e.g., after external change)."""
        self.config = new_config
        # Reset all editable fields
        if hasattr(self, "api_key_editable"):
            self.api_key_editable.reset(new_config.api_key)
            self.model_editable.reset(new_config.model)
            self.language_editable.reset(new_config.language)
            self.hotkey_selector.reset(new_config.hotkey)
            self.device_editable.reset(new_config.audio_device)
            self.auto_type_editable.reset(new_config.auto_type)
            self.auto_enter_editable.reset(new_config.auto_enter)
            self.typing_delay_editable.reset(str(new_config.typing_delay))
            self.history_enabled_editable.reset(new_config.history_enabled)
            self.history_days_editable.reset(str(new_config.history_days))
            self.notifications_editable.reset(new_config.notifications)
            self.backend_editable.reset(new_config.backend)
            self.debug_editable.reset(new_config.debug)
