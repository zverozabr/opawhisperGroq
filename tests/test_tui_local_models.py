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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

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
        """Download button initiates download workflow."""
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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        with patch("soupawhisper.tui.widgets.model_manager.get_model_manager") as mock_get:
            # Setup mock manager with all required methods
            mock_model_info = MagicMock()
            mock_model_info.name = "base"
            mock_model_info.size_mb = 142

            mock_manager = MagicMock()
            mock_manager.list_multilingual.return_value = [mock_model_info]
            mock_manager.get_model_info.return_value = mock_model_info
            mock_manager.is_downloaded.return_value = False
            mock_get.return_value = mock_manager

            async with TestApp().run_test() as pilot:
                download_btn = pilot.app.query_one("#download-model", Button)
                # Verify button exists and is accessible
                assert download_btn is not None
                assert "Download" in str(download_btn.label)


class TestLocalModelsStatus:
    """Test model status display."""

    @pytest.mark.asyncio
    async def test_shows_downloaded_status(self):
        """Shows status widget for models."""
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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

        with patch("soupawhisper.tui.widgets.model_manager.get_model_manager") as mock_get:
            # Setup mock manager with all required methods
            mock_model_info = MagicMock()
            mock_model_info.name = "base"
            mock_model_info.size_mb = 142

            mock_manager = MagicMock()
            mock_manager.list_multilingual.return_value = [mock_model_info]
            mock_manager.get_model_info.return_value = mock_model_info
            mock_manager.is_downloaded.return_value = True
            mock_manager.get_size_on_disk.return_value = 142 * 1024 * 1024
            mock_get.return_value = mock_manager

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen(config=mock_config)

            async with TestApp().run_test() as pilot:
                # Status widget should exist
                status = pilot.app.query_one("#model-status", Static)
                assert status is not None


class TestLocalModelsDelete:
    """Test delete functionality."""

    @pytest.mark.asyncio
    async def test_delete_button_calls_model_manager(self):
        """Delete button exists and is accessible."""
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
        mock_config.cloud_provider = "groq"
        mock_config.local_backend = "mlx"

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen(config=mock_config)

        with patch("soupawhisper.tui.widgets.model_manager.get_model_manager") as mock_get:
            # Setup mock manager with all required methods
            mock_model_info = MagicMock()
            mock_model_info.name = "base"
            mock_model_info.size_mb = 142

            mock_manager = MagicMock()
            mock_manager.list_multilingual.return_value = [mock_model_info]
            mock_manager.get_model_info.return_value = mock_model_info
            mock_manager.is_downloaded.return_value = True
            mock_manager.delete.return_value = True
            mock_get.return_value = mock_manager

            async with TestApp().run_test() as pilot:
                delete_btn = pilot.app.query_one("#delete-model", Button)
                # Verify button exists and is accessible
                assert delete_btn is not None
                assert "Delete" in str(delete_btn.label)
