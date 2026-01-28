"""Settings screen for application configuration.

Single Responsibility: Display and edit application settings.
SOLID/OCP: Uses SettingsRegistry for declarative settings.
"""

from typing import Callable, Optional

from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static, Switch

from soupawhisper.tui.settings_registry import (
    SETTINGS_REGISTRY,
    create_widget_for_setting,
    get_sections,
    get_settings_by_section,
)


def get_model_manager():
    """Get ModelManager instance.

    Lazy import to avoid circular dependencies.
    """
    from soupawhisper.providers.models import get_model_manager as _get

    return _get()


# DRY: Build field mappings from registry
def _build_field_mappings():
    """Build field mappings from registry."""
    mappings = {}
    for setting in SETTINGS_REGISTRY:
        if setting.widget_type == "select":
            widget_id = f"{setting.key.replace('_', '-')}-select"
        elif setting.widget_type == "hotkey":
            widget_id = f"{setting.key.replace('_', '-')}-input"
        else:
            widget_id = setting.key.replace("_", "-")
        mappings[widget_id] = setting.key
    return mappings


FIELD_MAPPINGS = _build_field_mappings()

# Fields that need type conversion - from registry
INT_FIELDS = {s.key for s in SETTINGS_REGISTRY if s.int_value}


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
        """Create settings UI.

        OCP: Generates UI from SettingsRegistry.
        Adding new settings only requires updating the registry.
        """
        # Generate sections from registry
        for section in get_sections():
            yield from self._compose_section_from_registry(section)

        # Local Models is a special section (not in registry)
        yield from self._compose_local_models_section()

    def _compose_section_from_registry(self, section: str):
        """Compose a section from registry settings.

        OCP: New settings appear automatically.
        """
        settings = get_settings_by_section(section)
        if not settings:
            return

        with Container(classes="section"):
            yield Static(section, classes="section-title")

            for setting in settings:
                with Horizontal(classes="field-row"):
                    yield Label(setting.label, classes="field-label")
                    widget = create_widget_for_setting(
                        setting,
                        self.config,
                        on_change=self._on_field_changed,
                    )
                    yield widget

    # NOTE: _compose_provider_section, _compose_recording_section,
    # _compose_output_section, _compose_advanced_section removed.
    # OCP: All these sections are now generated from SettingsRegistry.

    def _compose_local_models_section(self):
        """Compose local models settings section."""
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
        field_name = FIELD_MAPPINGS.get(event.select.id)
        if field_name:
            self._on_field_changed(field_name, event.value)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle Switch widget changes."""
        field_name = FIELD_MAPPINGS.get(event.switch.id)
        if field_name:
            self._on_field_changed(field_name, event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Input widget submission (Enter key)."""
        field_name = FIELD_MAPPINGS.get(event.input.id)
        if not field_name:
            return

        value = event.value
        if field_name in INT_FIELDS:
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
        """Download the selected local model using ModelManager."""
        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)
        progress = self.query_one("#download-progress", ProgressBar)

        model_name = str(model_select.value) if model_select.value else "base"
        status.update(f"Downloading {model_name}...")
        progress.update(progress=0.3)

        # Use ModelManager for real download
        try:
            manager = get_model_manager()
            # Determine download method based on provider
            provider = self._get_config("active_provider", "groq")
            if provider == "local-mlx":
                manager.download_for_mlx(model_name)
            else:
                manager.download_for_faster_whisper(model_name)

            self._finish_download(model_name)
        except Exception as e:
            status.update(f"Error: {e}")
            progress.update(progress=0)

    def _finish_download(self, model_name: str) -> None:
        """Finish download."""
        status = self.query_one("#model-status", Static)
        progress = self.query_one("#download-progress", ProgressBar)

        status.update(f"✓ {model_name} downloaded")
        progress.update(progress=1.0)

    def _delete_model(self) -> None:
        """Delete the selected local model using ModelManager."""
        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)

        model_name = str(model_select.value) if model_select.value else "base"
        status.update(f"Deleting {model_name}...")

        # Use ModelManager for real delete
        try:
            manager = get_model_manager()
            manager.delete(model_name)
            self._finish_delete(model_name)
        except Exception as e:
            status.update(f"Error: {e}")

    def _finish_delete(self, model_name: str) -> None:
        """Finish delete."""
        status = self.query_one("#model-status", Static)
        status.update("Not downloaded")

    def _update_model_status(self) -> None:
        """Update model status from ModelManager."""
        try:
            model_select = self.query_one("#local-model-select", Select)
            status = self.query_one("#model-status", Static)

            model_name = str(model_select.value) if model_select.value else "base"
            manager = get_model_manager()

            if manager.is_downloaded(model_name):
                status.update(f"✓ {model_name} downloaded")
            else:
                status.update("Not downloaded")
        except Exception:
            pass  # Ignore errors during status update
