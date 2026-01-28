"""Tests for StatusBar widget.

TDD: Tests written BEFORE implementation.
"""

import pytest
from textual.app import App, ComposeResult


class TestStatusBarStates:
    """Test StatusBar state transitions."""

    @pytest.mark.asyncio
    async def test_initial_state_is_ready(self):
        """Status bar shows 'Ready' on startup."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            assert not status.is_recording
            rendered = status.render()
            assert "Ready" in str(rendered) or "ready" in str(rendered).lower()

    @pytest.mark.asyncio
    async def test_recording_state_shows_rec(self):
        """Status bar shows 'REC' when recording."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            status.is_recording = True
            await pilot.pause()
            rendered = status.render()
            assert "REC" in str(rendered)

    @pytest.mark.asyncio
    async def test_recording_state_has_recording_class(self):
        """Recording state adds 'recording' CSS class."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            assert not status.has_class("recording")

            status.is_recording = True
            await pilot.pause()
            assert status.has_class("recording")

    @pytest.mark.asyncio
    async def test_stop_recording_removes_class(self):
        """Stopping recording removes 'recording' CSS class."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            status.is_recording = True
            await pilot.pause()
            assert status.has_class("recording")

            status.is_recording = False
            await pilot.pause()
            assert not status.has_class("recording")


class TestStatusBarTranscribing:
    """Test StatusBar transcribing state."""

    @pytest.mark.asyncio
    async def test_transcribing_state_shows_indicator(self):
        """Status bar shows transcribing indicator."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            status.is_transcribing = True
            await pilot.pause()
            rendered = status.render()
            # Should show some transcription indicator
            assert "Transcribing" in str(rendered) or "..." in str(rendered)


class TestStatusBarError:
    """Test StatusBar error state."""

    @pytest.mark.asyncio
    async def test_error_state_shows_message(self):
        """Status bar shows error message."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            status.error_message = "Permission denied"
            await pilot.pause()
            rendered = status.render()
            # Should show error indicator or message
            assert status.has_class("error") or "error" in str(rendered).lower()

    @pytest.mark.asyncio
    async def test_clear_error(self):
        """Clearing error returns to ready state."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar()

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            status.error_message = "Test error"
            await pilot.pause()

            status.error_message = ""
            await pilot.pause()
            assert not status.has_class("error")


class TestStatusBarHotkey:
    """Test StatusBar hotkey display."""

    @pytest.mark.asyncio
    async def test_shows_hotkey_hint(self):
        """Status bar shows configured hotkey."""
        from soupawhisper.tui.widgets.status_bar import StatusBar

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield StatusBar(hotkey="Ctrl+R")

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one(StatusBar)
            rendered = status.render()
            # Should show the hotkey somewhere
            assert "Ctrl" in str(rendered) or "hotkey" in str(rendered).lower()
