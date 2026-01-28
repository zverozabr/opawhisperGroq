"""Settings screen for application configuration.

Single Responsibility: Display and edit application settings.
"""

from typing import Callable, Optional

from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static, Switch

from soupawhisper.tui.widgets.hotkey_input import HotkeyInput


class SettingsScreen(VerticalScroll):
    """Screen for editing application settings.

    Organized into sections:
    - Provider: API provider, key, model, language
    - Recording: Hotkey, audio device
    - Output: Auto-type, auto-enter, typing delay
    - Advanced: Backend, debug mode
    """

    DEFAULT_CSS = """
    SettingsScreen {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    SettingsScreen .section {
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    SettingsScreen .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    SettingsScreen .field-row {
        height: 3;
        margin-bottom: 1;
    }

    SettingsScreen .field-label {
        width: 16;
        padding-top: 1;
    }

    SettingsScreen .field-input {
        width: 1fr;
    }
    """

    def __init__(
        self,
        config=None,
        on_save: Optional[Callable[[str, object], None]] = None,
        **kwargs
    ):
        """Initialize settings screen.

        Args:
            config: Config object with current settings.
            on_save: Callback when a field is saved (field_name, value).
        """
        super().__init__(**kwargs)
        self.config = config
        self._on_save = on_save

    def compose(self):
        """Create settings UI."""
        # Provider section
        with Container(classes="section"):
            yield Static("Provider", classes="section-title")

            with Horizontal(classes="field-row"):
                yield Label("Provider", classes="field-label")
                yield Select(
                    options=[
                        ("Groq", "groq"),
                        ("OpenAI", "openai"),
                        ("Local (MLX)", "local-mlx"),
                        ("Local (CPU)", "local-cpu"),
                    ],
                    value=self._get_config("active_provider", "groq"),
                    id="provider-select",
                    classes="field-input",
                )

            with Horizontal(classes="field-row"):
                yield Label("API Key", classes="field-label")
                yield Input(
                    value=self._get_config("api_key", ""),
                    password=True,
                    placeholder="Enter API key",
                    id="api-key",
                    classes="field-input",
                )

            with Horizontal(classes="field-row"):
                yield Label("Model", classes="field-label")
                yield Select(
                    options=[
                        ("whisper-large-v3", "whisper-large-v3"),
                        ("whisper-large-v3-turbo", "whisper-large-v3-turbo"),
                    ],
                    value=self._get_config("model", "whisper-large-v3"),
                    id="model-select",
                    classes="field-input",
                )

            with Horizontal(classes="field-row"):
                yield Label("Language", classes="field-label")
                yield Select(
                    options=[
                        ("Auto-detect", "auto"),
                        ("Russian", "ru"),
                        ("English", "en"),
                        ("German", "de"),
                        ("French", "fr"),
                        ("Spanish", "es"),
                    ],
                    value=self._get_config("language", "auto"),
                    id="language-select",
                    classes="field-input",
                )

        # Recording section
        with Container(classes="section"):
            yield Static("Recording", classes="section-title")

            with Horizontal(classes="field-row"):
                yield Label("Hotkey", classes="field-label")
                yield HotkeyInput(
                    hotkey=self._get_config("hotkey", "ctrl_r"),
                    on_change=lambda h: self._on_field_changed("hotkey", h),
                    id="hotkey-input",
                )

            with Horizontal(classes="field-row"):
                yield Label("Audio Device", classes="field-label")
                yield Select(
                    options=self._get_audio_device_options(),
                    value=self._get_config("audio_device", "default"),
                    id="audio-device-select",
                    classes="field-input",
                )

        # Output section
        with Container(classes="section"):
            yield Static("Output", classes="section-title")

            with Horizontal(classes="field-row"):
                yield Label("Auto-type", classes="field-label")
                yield Switch(
                    value=self._get_config("auto_type", True),
                    id="auto-type",
                )

            with Horizontal(classes="field-row"):
                yield Label("Auto-enter", classes="field-label")
                yield Switch(
                    value=self._get_config("auto_enter", False),
                    id="auto-enter",
                )

            with Horizontal(classes="field-row"):
                yield Label("Typing delay", classes="field-label")
                yield Input(
                    value=str(self._get_config("typing_delay", 12)),
                    placeholder="ms",
                    id="typing-delay",
                    classes="field-input",
                )

        # Advanced section
        with Container(classes="section"):
            yield Static("Advanced", classes="section-title")

            with Horizontal(classes="field-row"):
                yield Label("Debug mode", classes="field-label")
                yield Switch(
                    value=self._get_config("debug", False),
                    id="debug-mode",
                )

            with Horizontal(classes="field-row"):
                yield Label("Notifications", classes="field-label")
                yield Switch(
                    value=self._get_config("notifications", True),
                    id="notifications",
                )

        # Local Models section
        with Container(classes="section"):
            yield Static("Local Models", classes="section-title")

            with Horizontal(classes="field-row"):
                yield Label("Model", classes="field-label")
                yield Select(
                    options=self._get_local_model_options(),
                    value="base",
                    id="local-model-select",
                    classes="field-input",
                )

            with Horizontal(classes="field-row"):
                yield Label("Status", classes="field-label")
                yield Static("Not downloaded", id="model-status", classes="field-input")

            with Horizontal(classes="field-row"):
                yield Button("Download", id="download-model", variant="primary")
                yield Button("Delete", id="delete-model", variant="error")

            yield ProgressBar(id="download-progress", show_eta=False)

    def _get_local_model_options(self):
        """Get available local model options."""
        # Basic models list - in production would come from providers.models
        return [
            ("tiny (75 MB)", "tiny"),
            ("base (142 MB)", "base"),
            ("small (244 MB)", "small"),
            ("medium (769 MB)", "medium"),
            ("large-v3 (1.5 GB)", "large-v3"),
        ]

    def _get_audio_device_options(self):
        """Get available audio device options."""
        # Default option + platform-specific devices
        # In production, would enumerate actual devices
        return [
            ("Default", "default"),
            ("System Microphone", "system"),
        ]

    def _get_config(self, key: str, default):
        """Get config value safely.

        Args:
            key: Config key.
            default: Default value if config is None.

        Returns:
            Config value or default.
        """
        if self.config is None:
            return default
        return getattr(self.config, key, default)

    def _on_field_changed(self, field_name: str, value: object) -> None:
        """Handle field value change.

        Args:
            field_name: Name of the changed field.
            value: New value.
        """
        if self._on_save:
            self._on_save(field_name, value)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle Select widget changes."""
        field_map = {
            "provider-select": "active_provider",
            "model-select": "model",
            "language-select": "language",
            "audio-device-select": "audio_device",
        }
        field_name = field_map.get(event.select.id)
        if field_name:
            self._on_field_changed(field_name, event.value)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle Switch widget changes."""
        field_map = {
            "auto-type": "auto_type",
            "auto-enter": "auto_enter",
            "debug-mode": "debug",
            "notifications": "notifications",
        }
        field_name = field_map.get(event.switch.id)
        if field_name:
            self._on_field_changed(field_name, event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Input widget submission (Enter key)."""
        field_map = {
            "api-key": "api_key",
            "typing-delay": "typing_delay",
        }
        field_name = field_map.get(event.input.id)
        if field_name:
            value = event.value
            if field_name == "typing_delay":
                try:
                    value = int(value)
                except ValueError:
                    return
            self._on_field_changed(field_name, value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "download-model":
            self._download_model()
        elif event.button.id == "delete-model":
            self._delete_model()

    def _download_model(self) -> None:
        """Download the selected local model."""
        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)
        progress = self.query_one("#download-progress", ProgressBar)

        model_name = str(model_select.value) if model_select.value else "base"
        status.update(f"Downloading {model_name}...")
        progress.update(progress=0.5)

        # In production, would use ModelManager from providers.models
        # For now, just update status
        self.call_later(self._finish_download, model_name)

    def _finish_download(self, model_name: str) -> None:
        """Finish download simulation."""
        status = self.query_one("#model-status", Static)
        progress = self.query_one("#download-progress", ProgressBar)

        status.update(f"✓ {model_name} downloaded")
        progress.update(progress=1.0)

    def _delete_model(self) -> None:
        """Delete the selected local model."""
        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)

        model_name = str(model_select.value) if model_select.value else "base"
        status.update(f"Deleting {model_name}...")

        # In production, would use ModelManager from providers.models
        self.call_later(self._finish_delete, model_name)

    def _finish_delete(self, model_name: str) -> None:
        """Finish delete simulation."""
        status = self.query_one("#model-status", Static)
        status.update("Not downloaded")
