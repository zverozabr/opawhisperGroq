"""Tests for SettingsScreen.

TDD: Tests written BEFORE implementation.
"""

from unittest.mock import MagicMock

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Switch


def create_mock_config(**overrides):
    """Create a mock config with all required fields."""
    config = MagicMock()
    # Set all required fields with proper values
    config.active_provider = overrides.get("active_provider", "groq")
    config.api_key = overrides.get("api_key", "test_key")
    config.model = overrides.get("model", "whisper-large-v3")
    config.language = overrides.get("language", "auto")
    config.hotkey = overrides.get("hotkey", "ctrl_r")
    config.audio_device = overrides.get("audio_device", "default")
    config.auto_type = overrides.get("auto_type", True)
    config.auto_enter = overrides.get("auto_enter", False)
    config.typing_delay = overrides.get("typing_delay", 12)
    config.debug = overrides.get("debug", False)
    config.notifications = overrides.get("notifications", True)
    return config


class TestSettingsScreenCompose:
    """Test SettingsScreen widget composition."""

    @pytest.mark.asyncio
    async def test_has_provider_select(self):
        """SettingsScreen has provider selection."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            selects = pilot.app.query(Select)
            assert len(selects) >= 1

    @pytest.mark.asyncio
    async def test_has_api_key_input(self):
        """SettingsScreen has API key input."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            inputs = pilot.app.query(Input)
            # Should have at least API key input
            assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_has_auto_type_switch(self):
        """SettingsScreen has auto-type switch."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(auto_type=True)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            switches = pilot.app.query(Switch)
            assert len(switches) >= 1


class TestSettingsScreenValues:
    """Test SettingsScreen value display."""

    @pytest.mark.asyncio
    async def test_displays_current_provider(self):
        """SettingsScreen shows current provider."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="groq")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(SettingsScreen)
            # Provider should be accessible
            assert screen.config.active_provider == "groq"

    @pytest.mark.asyncio
    async def test_api_key_is_masked(self):
        """API key input is password-masked."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(api_key="secret_key_12345")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            api_input = pilot.app.query_one("#api-key", Input)
            assert api_input.password is True


class TestSettingsScreenSave:
    """Test SettingsScreen save functionality."""

    @pytest.mark.asyncio
    async def test_changing_provider_calls_save(self):
        """Changing provider triggers save callback."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()
        on_save = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config, on_save=on_save)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(SettingsScreen)
            # Simulate provider change
            screen._on_field_changed("active_provider", "openai")
            await pilot.pause()

            on_save.assert_called_with("active_provider", "openai")

    @pytest.mark.asyncio
    async def test_changing_auto_type_calls_save(self):
        """Toggling auto_type triggers save callback."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(auto_type=True)
        on_save = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config, on_save=on_save)

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(SettingsScreen)
            screen._on_field_changed("auto_type", False)
            await pilot.pause()

            on_save.assert_called_with("auto_type", False)


class TestSettingsScreenAudioDevice:
    """Test audio device selection in settings."""

    @pytest.mark.asyncio
    async def test_has_audio_device_select(self):
        """Settings has audio device selector."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Should have audio device select
            device_select = pilot.app.query("#audio-device-select")
            assert len(device_select) == 1


class TestSettingsScreenSections:
    """Test SettingsScreen section organization."""

    @pytest.mark.asyncio
    async def test_has_provider_section(self):
        """SettingsScreen has Provider section."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Check for provider-related widgets (ID from registry)
            provider_select = pilot.app.query_one("#active-provider-select", Select)
            assert provider_select is not None

    @pytest.mark.asyncio
    async def test_has_output_section(self):
        """SettingsScreen has Output section with switches."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(auto_type=True, auto_enter=False)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            auto_type_switch = pilot.app.query_one("#auto-type", Switch)
            assert auto_type_switch is not None
