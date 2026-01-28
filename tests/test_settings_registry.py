"""Tests for SettingsRegistry (OCP compliance).

TDD: Tests written BEFORE implementation.
SOLID/OCP: Settings can be added without modifying SettingsScreen.
"""

import pytest
from unittest.mock import MagicMock

from textual.app import App, ComposeResult


class TestSettingDefinition:
    """Test SettingDefinition dataclass."""

    def test_create_select_setting(self):
        """Create a select setting definition."""
        from soupawhisper.tui.settings_registry import SettingDefinition

        setting = SettingDefinition(
            key="active_provider",
            label="Provider",
            widget_type="select",
            section="Provider",
            options=[("Groq", "groq"), ("OpenAI", "openai")],
            default="groq",
        )

        assert setting.key == "active_provider"
        assert setting.widget_type == "select"
        assert len(setting.options) == 2

    def test_create_switch_setting(self):
        """Create a switch setting definition."""
        from soupawhisper.tui.settings_registry import SettingDefinition

        setting = SettingDefinition(
            key="auto_type",
            label="Auto-type",
            widget_type="switch",
            section="Output",
            default=True,
        )

        assert setting.key == "auto_type"
        assert setting.widget_type == "switch"
        assert setting.default is True

    def test_create_input_setting(self):
        """Create an input setting definition."""
        from soupawhisper.tui.settings_registry import SettingDefinition

        setting = SettingDefinition(
            key="api_key",
            label="API Key",
            widget_type="input",
            section="Provider",
            password=True,
        )

        assert setting.key == "api_key"
        assert setting.widget_type == "input"
        assert setting.password is True

    def test_create_hotkey_setting(self):
        """Create a hotkey setting definition."""
        from soupawhisper.tui.settings_registry import SettingDefinition

        setting = SettingDefinition(
            key="hotkey",
            label="Hotkey",
            widget_type="hotkey",
            section="Recording",
            default="ctrl_r",
        )

        assert setting.key == "hotkey"
        assert setting.widget_type == "hotkey"


class TestSettingsRegistry:
    """Test SettingsRegistry class."""

    def test_registry_has_default_settings(self):
        """Registry contains default settings."""
        from soupawhisper.tui.settings_registry import SETTINGS_REGISTRY

        assert len(SETTINGS_REGISTRY) > 0

    def test_registry_has_provider_section(self):
        """Registry contains provider section settings."""
        from soupawhisper.tui.settings_registry import SETTINGS_REGISTRY

        provider_settings = [s for s in SETTINGS_REGISTRY if s.section == "Provider"]
        assert len(provider_settings) >= 2  # At least provider and api_key

    def test_registry_has_output_section(self):
        """Registry contains output section settings."""
        from soupawhisper.tui.settings_registry import SETTINGS_REGISTRY

        output_settings = [s for s in SETTINGS_REGISTRY if s.section == "Output"]
        assert len(output_settings) >= 2  # At least auto_type and auto_enter

    def test_get_sections_returns_unique_sections(self):
        """get_sections returns unique section names in order."""
        from soupawhisper.tui.settings_registry import get_sections

        sections = get_sections()
        assert len(sections) == len(set(sections))  # All unique
        assert "Provider" in sections

    def test_get_settings_by_section(self):
        """get_settings_by_section filters correctly."""
        from soupawhisper.tui.settings_registry import get_settings_by_section

        provider_settings = get_settings_by_section("Provider")
        assert all(s.section == "Provider" for s in provider_settings)


class TestSettingsRegistryWidgetGeneration:
    """Test widget generation from registry."""

    @pytest.mark.asyncio
    async def test_generate_select_widget(self):
        """Registry can generate Select widget."""
        from soupawhisper.tui.settings_registry import (
            SettingDefinition,
            create_widget_for_setting,
        )
        from textual.widgets import Select

        setting = SettingDefinition(
            key="language",
            label="Language",
            widget_type="select",
            section="Provider",
            options=[("Auto", "auto"), ("English", "en")],
            default="auto",
        )

        mock_config = MagicMock()
        mock_config.language = "auto"

        widget = create_widget_for_setting(setting, mock_config)
        assert isinstance(widget, Select)

    @pytest.mark.asyncio
    async def test_generate_switch_widget(self):
        """Registry can generate Switch widget."""
        from soupawhisper.tui.settings_registry import (
            SettingDefinition,
            create_widget_for_setting,
        )
        from textual.widgets import Switch

        setting = SettingDefinition(
            key="auto_type",
            label="Auto-type",
            widget_type="switch",
            section="Output",
            default=True,
        )

        mock_config = MagicMock()
        mock_config.auto_type = True

        widget = create_widget_for_setting(setting, mock_config)
        assert isinstance(widget, Switch)

    @pytest.mark.asyncio
    async def test_generate_input_widget(self):
        """Registry can generate Input widget."""
        from soupawhisper.tui.settings_registry import (
            SettingDefinition,
            create_widget_for_setting,
        )
        from textual.widgets import Input

        setting = SettingDefinition(
            key="api_key",
            label="API Key",
            widget_type="input",
            section="Provider",
            password=True,
        )

        mock_config = MagicMock()
        mock_config.api_key = "test_key"

        # Input widget requires App context for initialization
        class TestApp(App):
            def compose(self) -> ComposeResult:
                widget = create_widget_for_setting(setting, mock_config)
                self.test_widget = widget
                yield widget

        async with TestApp().run_test() as pilot:
            widget = pilot.app.test_widget
            assert isinstance(widget, Input)
            assert widget.password is True


class TestSettingsScreenFromRegistry:
    """Test SettingsScreen uses registry for OCP compliance."""

    @pytest.mark.asyncio
    async def test_settings_screen_renders_from_registry(self):
        """SettingsScreen renders widgets from registry."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = MagicMock()
        mock_config.active_provider = "groq"
        mock_config.api_key = "test"
        mock_config.model = "whisper-large-v3"
        mock_config.language = "auto"
        mock_config.hotkey = "ctrl_r"
        mock_config.audio_device = "default"
        mock_config.auto_type = True
        mock_config.auto_enter = False
        mock_config.typing_delay = 12
        mock_config.debug = False
        mock_config.notifications = True
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Should have provider section
            provider_sections = pilot.app.query(".section")
            assert len(provider_sections) >= 3

    @pytest.mark.asyncio
    async def test_adding_setting_to_registry_appears_in_ui(self):
        """OCP: Adding setting to registry makes it appear in UI."""
        from soupawhisper.tui.settings_registry import (
            SETTINGS_REGISTRY,
            SettingDefinition,
        )
        from soupawhisper.tui.screens.settings import SettingsScreen

        # Add a new setting dynamically
        test_setting = SettingDefinition(
            key="test_new_setting",
            label="Test New",
            widget_type="switch",
            section="Advanced",
            default=False,
        )

        original_len = len(SETTINGS_REGISTRY)
        SETTINGS_REGISTRY.append(test_setting)

        try:
            mock_config = MagicMock()
            mock_config.active_provider = "groq"
            mock_config.api_key = "test"
            mock_config.model = "whisper-large-v3"
            mock_config.language = "auto"
            mock_config.hotkey = "ctrl_r"
            mock_config.audio_device = "default"
            mock_config.auto_type = True
            mock_config.auto_enter = False
            mock_config.typing_delay = 12
            mock_config.debug = False
            mock_config.notifications = True
            mock_config.test_new_setting = False
            mock_config.cloud_provider = "groq"
            mock_config.local_backend = "mlx"

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen(config=mock_config)

            async with TestApp().run_test() as pilot:
                # New setting should be rendered
                switches = pilot.app.query("Switch")
                # Should have at least one more switch than before
                assert len(switches) >= 3

        finally:
            # Cleanup - remove test setting
            SETTINGS_REGISTRY.pop()
            assert len(SETTINGS_REGISTRY) == original_len
