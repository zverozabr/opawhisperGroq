"""Tests for TUIApp.

TDD: Tests written BEFORE implementation.
"""

from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import TabbedContent, TabPane, Footer, Header


@pytest.fixture
def mock_config():
    """Create mock config for testing."""
    config = MagicMock()
    config.hotkey = "ctrl_r"
    config.history_days = 3
    config.history_enabled = True
    config.debug = False
    config.api_key = "test_key"
    config.active_provider = "groq"
    config.model = "whisper-large-v3"
    config.language = "auto"
    config.auto_type = True
    config.auto_enter = False
    config.typing_delay = 12
    config.notifications = True
    return config


@pytest.fixture
def tui_app_patched(mock_config):
    """Create patched TUIApp for testing."""
    with patch("soupawhisper.tui.app.Config.load", return_value=mock_config):
        with patch("soupawhisper.tui.app.HistoryStorage") as mock_history:
            mock_history.return_value.get_recent.return_value = []
            from soupawhisper.tui.app import TUIApp
            app = TUIApp(test_mode=True)
            yield app


class TestTUIAppCompose:
    """Test TUIApp widget composition."""

    @pytest.mark.asyncio
    async def test_app_has_header(self, tui_app_patched):
        """TUIApp has a header."""
        async with tui_app_patched.run_test() as pilot:
            headers = pilot.app.query(Header)
            assert len(headers) == 1

    @pytest.mark.asyncio
    async def test_app_has_footer(self, tui_app_patched):
        """TUIApp has a footer with keybindings."""
        async with tui_app_patched.run_test() as pilot:
            footers = pilot.app.query(Footer)
            assert len(footers) == 1

    @pytest.mark.asyncio
    async def test_app_has_status_bar(self, tui_app_patched):
        """TUIApp has StatusBar widget."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        async with tui_app_patched.run_test() as pilot:
            status_bars = pilot.app.query(StatusBar)
            assert len(status_bars) == 1

    @pytest.mark.asyncio
    async def test_app_has_tabbed_content(self, tui_app_patched):
        """TUIApp has TabbedContent for navigation."""
        async with tui_app_patched.run_test() as pilot:
            tabs = pilot.app.query(TabbedContent)
            assert len(tabs) == 1


class TestTUIAppTabs:
    """Test TUIApp tab navigation."""

    @pytest.mark.asyncio
    async def test_has_history_tab(self, tui_app_patched):
        """TUIApp has History tab."""
        async with tui_app_patched.run_test() as pilot:
            # Check tab panes exist
            history_pane = pilot.app.query_one("#history-tab", TabPane)
            assert history_pane is not None

    @pytest.mark.asyncio
    async def test_has_settings_tab(self, tui_app_patched):
        """TUIApp has Settings tab."""
        async with tui_app_patched.run_test() as pilot:
            settings_pane = pilot.app.query_one("#settings-tab", TabPane)
            assert settings_pane is not None

    @pytest.mark.asyncio
    async def test_history_tab_is_default(self, tui_app_patched):
        """History tab is selected by default."""
        async with tui_app_patched.run_test() as pilot:
            tabs = pilot.app.query_one(TabbedContent)
            # First tab should be active
            assert tabs.active == "history-tab"


class TestTUIAppKeybindings:
    """Test TUIApp keyboard bindings."""

    @pytest.mark.asyncio
    async def test_q_quits(self, tui_app_patched):
        """Pressing 'q' quits the application."""
        async with tui_app_patched.run_test() as pilot:
            await pilot.press("q")
            # App should be exiting
            assert tui_app_patched._exit

    @pytest.mark.asyncio
    async def test_h_switches_to_history(self, tui_app_patched):
        """Pressing 'h' switches to History tab."""
        async with tui_app_patched.run_test() as pilot:
            # First go to settings
            await pilot.press("s")
            await pilot.pause()

            # Then press h to go back to history
            await pilot.press("h")
            await pilot.pause()

            tabs = pilot.app.query_one(TabbedContent)
            assert tabs.active == "history-tab"

    @pytest.mark.asyncio
    async def test_s_switches_to_settings(self, tui_app_patched):
        """Pressing 's' switches to Settings tab."""
        async with tui_app_patched.run_test() as pilot:
            await pilot.press("s")
            await pilot.pause()

            tabs = pilot.app.query_one(TabbedContent)
            assert tabs.active == "settings-tab"


class TestTUIAppTitle:
    """Test TUIApp title and branding."""

    @pytest.mark.asyncio
    async def test_app_has_title(self, tui_app_patched):
        """TUIApp has correct title."""
        assert tui_app_patched.TITLE == "SoupaWhisper"

    @pytest.mark.asyncio
    async def test_app_has_subtitle(self, tui_app_patched):
        """TUIApp has subtitle."""
        # Subtitle should exist
        assert hasattr(tui_app_patched, "SUB_TITLE") or hasattr(tui_app_patched, "SUBTITLE")
