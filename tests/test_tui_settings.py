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
    # New fields for Cloud/Local toggle
    config.cloud_provider = overrides.get("cloud_provider", "groq")
    config.local_backend = overrides.get("local_backend", "mlx")
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


class TestAudioDeviceOptions:
    """TDD: Test dynamic audio device options."""

    def test_get_audio_device_options_returns_list(self):
        """get_audio_device_options returns list of tuples."""
        from soupawhisper.tui.settings_registry import get_audio_device_options

        options = get_audio_device_options()

        assert isinstance(options, list)
        assert len(options) >= 1  # At least default
        assert all(isinstance(o, tuple) and len(o) == 2 for o in options)

    def test_get_audio_device_options_has_names_and_ids(self):
        """Each option has (name, id) format."""
        from soupawhisper.tui.settings_registry import get_audio_device_options

        options = get_audio_device_options()

        for name, device_id in options:
            assert isinstance(name, str)
            assert isinstance(device_id, str)
            assert len(name) > 0
            assert len(device_id) > 0

    def test_callable_options_in_registry(self):
        """audio_device setting uses callable for options."""
        from soupawhisper.tui.settings_registry import SETTINGS_REGISTRY

        audio_device_setting = next(
            (s for s in SETTINGS_REGISTRY if s.key == "audio_device"), None
        )

        assert audio_device_setting is not None
        # Options should be callable (dynamic)
        assert callable(audio_device_setting.options)

    @pytest.mark.asyncio
    async def test_audio_device_select_has_real_options(self):
        """Audio device dropdown shows real devices from system."""
        from unittest.mock import patch

        from soupawhisper.audio import AudioDevice
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()
        mock_devices = [
            AudioDevice(id="0", name="MacBook Pro Microphone"),
            AudioDevice(id="1", name="External USB Mic"),
        ]

        with patch(
            "soupawhisper.audio.AudioRecorder.list_devices",
            return_value=mock_devices,
        ):

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen(config=mock_config)

            async with TestApp().run_test() as pilot:
                device_select = pilot.app.query_one("#audio-device-select", Select)

                # Should have 2 options (from mock devices)
                # Note: _options contains tuples of (ContentRenderable, value)
                option_values = [opt[1] for opt in device_select._options]
                assert "0" in option_values
                assert "1" in option_values


class TestSettingsScreenSections:
    """Test SettingsScreen section organization."""

    @pytest.mark.asyncio
    async def test_has_provider_section(self):
        """SettingsScreen has Provider section."""
        from soupawhisper.tui.screens.settings import SettingsScreen
        from textual.containers import Container

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Check for provider section
            provider_section = pilot.app.query_one("#provider-section", Container)
            assert provider_section is not None

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


class TestProviderModeToggle:
    """TDD: Test provider mode toggle (Cloud/Local)."""

    @pytest.mark.asyncio
    async def test_has_local_mode_switch(self):
        """Provider section has local mode toggle switch."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="groq")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Should have local mode switch
            switch = pilot.app.query_one("#local-mode-switch", Switch)
            assert switch is not None
            # Cloud mode by default
            assert switch.value is False

    @pytest.mark.asyncio
    async def test_local_mode_switch_true_for_local_provider(self):
        """Switch is ON when local provider is active."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="local-mlx")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            switch = pilot.app.query_one("#local-mode-switch", Switch)
            assert switch.value is True

    @pytest.mark.asyncio
    async def test_has_provider_tabs(self):
        """Provider section has Cloud/Local tabs."""
        from textual.widgets import TabbedContent, TabPane

        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            tabs = pilot.app.query_one("#provider-tabs", TabbedContent)
            assert tabs is not None

            # Should have both tabs
            cloud_tab = pilot.app.query_one("#cloud-tab", TabPane)
            local_tab = pilot.app.query_one("#local-tab", TabPane)
            assert cloud_tab is not None
            assert local_tab is not None

    @pytest.mark.asyncio
    async def test_switch_toggles_active_tab(self):
        """Toggling switch changes active tab."""
        from textual.widgets import TabbedContent

        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="groq")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            tabs = pilot.app.query_one("#provider-tabs", TabbedContent)
            switch = pilot.app.query_one("#local-mode-switch", Switch)

            # Initially cloud tab is active
            assert tabs.active == "cloud-tab"

            # Toggle to local
            switch.value = True
            await pilot.pause()

            assert tabs.active == "local-tab"

    @pytest.mark.asyncio
    async def test_cloud_tab_has_api_settings(self):
        """Cloud tab contains API Key and cloud provider select."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="groq")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Cloud tab should have API key input
            api_input = pilot.app.query_one("#api-key", Input)
            assert api_input is not None
            assert api_input.password is True

            # And cloud provider select
            provider_select = pilot.app.query_one("#cloud-provider-select", Select)
            assert provider_select is not None

    @pytest.mark.asyncio
    async def test_local_tab_has_model_download(self):
        """Local tab contains model select and download button."""
        from textual.widgets import Button

        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="local-mlx")

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            # Local tab should have model select
            model_select = pilot.app.query_one("#local-model-select", Select)
            assert model_select is not None

            # And download button
            download_btn = pilot.app.query_one("#download-model", Button)
            assert download_btn is not None

    @pytest.mark.asyncio
    async def test_switch_saves_provider(self):
        """Toggling switch saves provider setting."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = create_mock_config(active_provider="groq")
        on_save = MagicMock()

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config, on_save=on_save)

        async with TestApp().run_test() as pilot:
            switch = pilot.app.query_one("#local-mode-switch", Switch)

            # Toggle to local
            switch.value = True
            await pilot.pause()

            # Should save provider change
            on_save.assert_called()
            # Check it was called with active_provider
            call_args = [call[0] for call in on_save.call_args_list]
            assert any("active_provider" in str(args) for args in call_args)
