"""Settings screen for application configuration.

Single Responsibility: Display and edit application settings.
SOLID/OCP: Uses SettingsRegistry for declarative settings.
"""

from typing import Callable, Optional

from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Button,
    Input,
    Label,
    Select,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from soupawhisper.tui.settings_registry import (
    SETTINGS_REGISTRY,
    create_widget_for_setting,
    get_sections,
    get_settings_by_section,
)
from soupawhisper.tui.widgets.model_manager import ModelManagerWidget


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
        height: auto;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    SettingsScreen .section-title {
        text-style: bold;
        margin-bottom: 1;
        color: $text;
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

    /* HotkeyCapture widget inside field-row */
    SettingsScreen HotkeyCapture {
        width: 1fr;
        height: 3;
        layout: horizontal;
    }

    SettingsScreen HotkeyCapture #hotkey-display {
        width: 1fr;
        height: 3;
        padding: 0 1;
        background: $surface;
        content-align: left middle;
    }

    SettingsScreen HotkeyCapture #set-hotkey-btn {
        width: 10;
        height: 3;
    }

    /* Mode toggle label */
    SettingsScreen .mode-label {
        padding-left: 1;
        padding-top: 1;
        color: $text;
    }

    /* Provider tabs */
    SettingsScreen #provider-tabs {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }

    SettingsScreen TabPane {
        padding: 1;
    }

    SettingsScreen .model-status {
        padding-top: 1;
    }

    SettingsScreen .model-status.-downloaded {
        color: $success;
    }

    SettingsScreen .model-status.-not-downloaded {
        color: $text-muted;
    }

    SettingsScreen .button-row {
        height: auto;
        margin-top: 1;
    }

    SettingsScreen .button-row Button {
        margin-right: 1;
    }

    SettingsScreen ProgressBar {
        margin-top: 1;
        height: 1;
    }

    SettingsScreen ProgressBar.-hidden {
        display: none;
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
            if section == "Provider":
                # Provider section includes local model controls
                yield from self._compose_provider_section_with_local_models()
            else:
                yield from self._compose_section_from_registry(section)

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

    def _compose_provider_section_with_local_models(self):
        """Compose Provider section with Toggle and Tabs.

        UI Structure:
        - Mode switch (Cloud/Local)
        - TabbedContent with Cloud and Local tabs
        - Language selector (common)
        """
        is_local = self._is_local_provider()
        initial_tab = "local-tab" if is_local else "cloud-tab"

        with Container(classes="section", id="provider-section"):
            yield Static("Provider", classes="section-title")

            # Mode toggle: Cloud / Local
            with Horizontal(classes="field-row"):
                yield Label("Mode", classes="field-label")
                yield Switch(value=is_local, id="local-mode-switch")
                mode_text = "Local" if is_local else "Cloud"
                yield Static(mode_text, id="mode-label", classes="mode-label")

            # Tabs for Cloud / Local settings
            with TabbedContent(initial=initial_tab, id="provider-tabs"):
                with TabPane("Cloud", id="cloud-tab"):
                    yield from self._compose_cloud_tab()

                with TabPane("Local", id="local-tab"):
                    yield from self._compose_local_tab()

            # Language is common for both modes
            yield from self._compose_language_field()

    def _compose_cloud_tab(self):
        """Compose Cloud tab content: Provider, API Key, Model."""
        settings = get_settings_by_section("Provider")

        for setting in settings:
            if setting.key == "cloud_provider":
                with Horizontal(classes="field-row"):
                    yield Label("Provider", classes="field-label")
                    yield Select(
                        options=[("Groq", "groq"), ("OpenAI", "openai")],
                        value=self._get_config("cloud_provider", "groq"),
                        id="cloud-provider-select",
                        classes="field-input",
                    )
            elif setting.key == "api_key":
                with Horizontal(classes="field-row"):
                    yield Label("API Key", classes="field-label")
                    yield Input(
                        value=self._get_config("api_key", ""),
                        password=True,
                        placeholder="Enter API key",
                        id="api-key",
                        classes="field-input",
                    )
            elif setting.key == "model":
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

    def _compose_local_tab(self):
        """Compose Local tab content: Backend, Model, Download controls."""
        yield ModelManagerWidget(
            get_config=self._get_config,
            on_local_backend_change=self._on_local_backend_change,
        )

    def _compose_language_field(self):
        """Compose language selector (common for Cloud and Local)."""
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

    def _is_local_provider(self) -> bool:
        """Check if current provider is local (MLX or CPU)."""
        if self.config is None:
            return False
        provider = getattr(self.config, "active_provider", "groq")
        return provider in ("local-mlx", "local-cpu")

    def _on_local_backend_change(self, value: str) -> None:
        """Handle local backend change from ModelManagerWidget."""
        self._on_field_changed("local_backend", value)
        if self._is_local_provider():
            self._on_field_changed("active_provider", f"local-{value}")

    def _on_mode_switch_changed(self, is_local: bool) -> None:
        """Handle mode switch change (Cloud/Local).

        Args:
            is_local: True if Local mode selected
        """
        try:
            # Switch active tab
            tabs = self.query_one("#provider-tabs", TabbedContent)
            tabs.active = "local-tab" if is_local else "cloud-tab"

            # Update mode label
            mode_label = self.query_one("#mode-label", Static)
            mode_label.update("Local" if is_local else "Cloud")

            # Determine active provider
            if is_local:
                backend = self._get_config("local_backend", "mlx")
                provider = f"local-{backend}"
            else:
                provider = self._get_config("cloud_provider", "groq")

            # Save active provider
            self._on_field_changed("active_provider", provider)

            if is_local:
                try:
                    model_widget = self.query_one(ModelManagerWidget)
                    model_widget.update_model_status()
                except Exception:
                    pass
        except Exception:
            pass

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
        # Handle cloud provider change - update active_provider
        if event.select.id == "cloud-provider-select":
            self._on_field_changed("cloud_provider", event.value)
            # Also update active_provider if in cloud mode
            if not self._is_local_provider():
                self._on_field_changed("active_provider", event.value)
            return

        field_name = FIELD_MAPPINGS.get(event.select.id)
        if field_name:
            self._on_field_changed(field_name, event.value)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle Switch widget changes."""
        # Handle mode switch specially
        if event.switch.id == "local-mode-switch":
            self._on_mode_switch_changed(event.value)
            return

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
        return

    # Model management UI is handled by ModelManagerWidget.
