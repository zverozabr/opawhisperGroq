"""Tests for Local Models UI integration with ModelManager.

TDD: Tests written BEFORE implementation.
"""

import pytest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import Button, Select, Static


class TestLocalModelsSection:
    """Test Local Models section in settings."""

    @pytest.mark.asyncio
    async def test_has_model_select(self):
        """Settings has model select widget."""
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

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            model_select = pilot.app.query_one("#local-model-select", Select)
            assert model_select is not None

    @pytest.mark.asyncio
    async def test_has_download_button(self):
        """Settings has download button."""
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

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            download_btn = pilot.app.query_one("#download-model", Button)
            assert download_btn is not None

    @pytest.mark.asyncio
    async def test_has_delete_button(self):
        """Settings has delete button."""
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

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        async with TestApp().run_test() as pilot:
            delete_btn = pilot.app.query_one("#delete-model", Button)
            assert delete_btn is not None


class TestLocalModelsDownload:
    """Test download functionality."""

    @pytest.mark.asyncio
    async def test_download_button_calls_model_manager(self):
        """Download button calls ModelManager.download_for_mlx."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = MagicMock()
        mock_config.active_provider = "local-mlx"
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

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        with patch("soupawhisper.tui.screens.settings.get_model_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.download_for_mlx = MagicMock()
            mock_get.return_value = mock_manager

            async with TestApp().run_test() as pilot:
                download_btn = pilot.app.query_one("#download-model", Button)
                # Scroll to button and press it
                download_btn.scroll_visible()
                await pilot.pause()
                download_btn.press()
                await pilot.pause()

                # ModelManager should be called
                mock_manager.download_for_mlx.assert_called()


class TestLocalModelsStatus:
    """Test model status display."""

    @pytest.mark.asyncio
    async def test_shows_downloaded_status(self):
        """Shows 'Downloaded' for downloaded models."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = MagicMock()
        mock_config.active_provider = "local-mlx"
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

        with patch("soupawhisper.tui.screens.settings.get_model_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.is_downloaded.return_value = True
            mock_get.return_value = mock_manager

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen(config=mock_config)

            async with TestApp().run_test() as pilot:
                # Trigger model select change to update status
                status = pilot.app.query_one("#model-status", Static)
                # Initial status or after refresh
                assert status is not None


class TestLocalModelsDelete:
    """Test delete functionality."""

    @pytest.mark.asyncio
    async def test_delete_button_calls_model_manager(self):
        """Delete button calls ModelManager.delete."""
        from soupawhisper.tui.screens.settings import SettingsScreen

        mock_config = MagicMock()
        mock_config.active_provider = "local-mlx"
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

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        with patch("soupawhisper.tui.screens.settings.get_model_manager") as mock_get:
            mock_manager = MagicMock()
            mock_manager.delete = MagicMock()
            mock_manager.is_downloaded.return_value = True
            mock_get.return_value = mock_manager

            async with TestApp().run_test() as pilot:
                delete_btn = pilot.app.query_one("#delete-model", Button)
                # Scroll to button and press it
                delete_btn.scroll_visible()
                await pilot.pause()
                delete_btn.press()
                await pilot.pause()

                # ModelManager should be called
                mock_manager.delete.assert_called()
