"""Settings tab component with inline field saving."""

from typing import Callable

import flet as ft

from soupawhisper.audio import AudioRecorder
from soupawhisper.config import Config

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

        # Audio device dropdown
        devices = self._get_audio_devices()
        device_dropdown = ft.Dropdown(
            label="Microphone",
            value=self.config.audio_device,
            options=[ft.dropdown.Option(key=d[0], text=d[1]) for d in devices],
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
                        SettingsSection("API", [self.api_key_editable]),
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
                        SettingsSection("Developer", [self.debug_editable]),
                    ],
                    spacing=12,
                ),
                padding=16,
            )
        ]

        return self

    def _get_audio_devices(self) -> list[tuple[str, str]]:
        """Get list of available audio devices."""
        devices = [("default", "Default")]
        try:
            for device in AudioRecorder.list_devices():
                devices.append((device.id, device.name))
        except Exception:
            pass
        return devices

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
        try:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Saved"),
                    duration=1000,
                )
                self.page.snack_bar.open = True
                self.page.update()
        except RuntimeError:
            pass

    def update_config(self, new_config: Config) -> None:
        """Update all fields from new config (e.g., after external change)."""
        self.config = new_config
        # Reset all editable fields
        if hasattr(self, "api_key_editable"):
            self.api_key_editable.reset(new_config.api_key)
            self.language_editable.reset(new_config.language)
            self.hotkey_selector.reset(new_config.hotkey)
            self.device_editable.reset(new_config.audio_device)
            self.auto_type_editable.reset(new_config.auto_type)
            self.auto_enter_editable.reset(new_config.auto_enter)
            self.typing_delay_editable.reset(str(new_config.typing_delay))
            self.history_enabled_editable.reset(new_config.history_enabled)
            self.history_days_editable.reset(str(new_config.history_days))
            self.debug_editable.reset(new_config.debug)
