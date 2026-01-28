"""Settings Registry for declarative UI generation.

SOLID/OCP: Add settings without modifying SettingsScreen.
DRY: Single source of truth for setting definitions.
KISS: Simple dataclass-based registry.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from textual.widgets import Input, Select, Switch

# Avoid circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from soupawhisper.config import Config


WidgetType = Literal["select", "switch", "input", "hotkey"]


@dataclass
class SettingDefinition:
    """Definition of a single setting.

    Attributes:
        key: Config attribute name.
        label: Display label.
        widget_type: Type of widget to render.
        section: Section name for grouping.
        options: Options for select widget (label, value) tuples.
        default: Default value.
        password: For input widget, mask input.
        placeholder: For input widget, placeholder text.
        int_value: For input widget, parse as int.
    """

    key: str
    label: str
    widget_type: WidgetType
    section: str
    options: list[tuple[str, str]] = field(default_factory=list)
    default: Any = None
    password: bool = False
    placeholder: str = ""
    int_value: bool = False


# =============================================================================
# Settings Registry - Single source of truth
# =============================================================================

SETTINGS_REGISTRY: list[SettingDefinition] = [
    # Provider section
    SettingDefinition(
        key="active_provider",
        label="Provider",
        widget_type="select",
        section="Provider",
        options=[
            ("Groq", "groq"),
            ("OpenAI", "openai"),
            ("Local (MLX)", "local-mlx"),
            ("Local (CPU)", "local-cpu"),
        ],
        default="groq",
    ),
    SettingDefinition(
        key="api_key",
        label="API Key",
        widget_type="input",
        section="Provider",
        password=True,
        placeholder="Enter API key",
    ),
    SettingDefinition(
        key="model",
        label="Model",
        widget_type="select",
        section="Provider",
        options=[
            ("whisper-large-v3", "whisper-large-v3"),
            ("whisper-large-v3-turbo", "whisper-large-v3-turbo"),
        ],
        default="whisper-large-v3",
    ),
    SettingDefinition(
        key="language",
        label="Language",
        widget_type="select",
        section="Provider",
        options=[
            ("Auto-detect", "auto"),
            ("Russian", "ru"),
            ("English", "en"),
            ("German", "de"),
            ("French", "fr"),
            ("Spanish", "es"),
        ],
        default="auto",
    ),
    # Recording section
    SettingDefinition(
        key="hotkey",
        label="Hotkey",
        widget_type="hotkey",
        section="Recording",
        default="ctrl_r",
    ),
    SettingDefinition(
        key="audio_device",
        label="Audio Device",
        widget_type="select",
        section="Recording",
        options=[("Default", "default")],  # Dynamic options
        default="default",
    ),
    # Output section
    SettingDefinition(
        key="auto_type",
        label="Auto-type",
        widget_type="switch",
        section="Output",
        default=True,
    ),
    SettingDefinition(
        key="auto_enter",
        label="Auto-enter",
        widget_type="switch",
        section="Output",
        default=False,
    ),
    SettingDefinition(
        key="typing_delay",
        label="Typing delay",
        widget_type="input",
        section="Output",
        placeholder="ms",
        int_value=True,
        default=12,
    ),
    # Advanced section
    SettingDefinition(
        key="debug",
        label="Debug mode",
        widget_type="switch",
        section="Advanced",
        default=False,
    ),
    SettingDefinition(
        key="notifications",
        label="Notifications",
        widget_type="switch",
        section="Advanced",
        default=True,
    ),
]


def get_sections() -> list[str]:
    """Get unique section names in order of appearance.

    Returns:
        List of section names.
    """
    seen = set()
    sections = []
    for setting in SETTINGS_REGISTRY:
        if setting.section not in seen:
            seen.add(setting.section)
            sections.append(setting.section)
    return sections


def get_settings_by_section(section: str) -> list[SettingDefinition]:
    """Get settings for a specific section.

    Args:
        section: Section name.

    Returns:
        List of settings in that section.
    """
    return [s for s in SETTINGS_REGISTRY if s.section == section]


def create_widget_for_setting(
    setting: SettingDefinition,
    config: "Config",
    on_change: Optional[Callable[[str, Any], None]] = None,
):
    """Create appropriate widget for a setting.

    Args:
        setting: Setting definition.
        config: Config object to get current value.
        on_change: Callback when value changes.

    Returns:
        Textual widget instance.
    """
    current_value = getattr(config, setting.key, setting.default)

    if setting.widget_type == "select":
        return Select(
            options=setting.options,
            value=current_value,
            id=f"{setting.key.replace('_', '-')}-select",
            classes="field-input",
        )

    elif setting.widget_type == "switch":
        return Switch(
            value=bool(current_value),
            id=setting.key.replace("_", "-"),
        )

    elif setting.widget_type == "input":
        return Input(
            value=str(current_value) if current_value else "",
            password=setting.password,
            placeholder=setting.placeholder,
            id=setting.key.replace("_", "-"),
            classes="field-input",
        )

    elif setting.widget_type == "hotkey":
        # Import here to avoid circular import
        from soupawhisper.tui.widgets.hotkey_input import HotkeyInput

        return HotkeyInput(
            hotkey=str(current_value),
            on_change=lambda h: on_change(setting.key, h) if on_change else None,
            id=f"{setting.key.replace('_', '-')}-input",
        )

    else:
        raise ValueError(f"Unknown widget type: {setting.widget_type}")
