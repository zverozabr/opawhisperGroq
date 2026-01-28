"""Tests for WaveformWidget.

TDD: Tests written BEFORE implementation.
"""


import pytest
from textual.app import App, ComposeResult


class TestWaveformWidget:
    """Test WaveformWidget display."""

    @pytest.mark.asyncio
    async def test_widget_exists(self):
        """WaveformWidget can be imported."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        assert WaveformWidget is not None

    @pytest.mark.asyncio
    async def test_widget_renders(self):
        """WaveformWidget renders without errors."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            assert waveform is not None

    @pytest.mark.asyncio
    async def test_widget_hidden_by_default(self):
        """WaveformWidget is hidden when not recording."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            # Should be hidden initially
            assert not waveform.is_visible


class TestWaveformWidgetRecording:
    """Test WaveformWidget during recording."""

    @pytest.mark.asyncio
    async def test_shows_when_recording_starts(self):
        """WaveformWidget shows when recording starts."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            await pilot.pause()
            assert waveform.is_visible

    @pytest.mark.asyncio
    async def test_hides_when_recording_stops(self):
        """WaveformWidget hides when recording stops."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            await pilot.pause()
            waveform.stop_recording()
            await pilot.pause()
            assert not waveform.is_visible


class TestWaveformWidgetData:
    """Test WaveformWidget data handling."""

    @pytest.mark.asyncio
    async def test_update_level_adds_data(self):
        """update_level adds data to widget."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            waveform.update_level(0.5)
            await pilot.pause()
            assert len(waveform._data) > 0

    @pytest.mark.asyncio
    async def test_update_level_normalizes_value(self):
        """update_level normalizes value to 0-1 range."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            waveform.update_level(1.5)  # Above max
            waveform.update_level(-0.5)  # Below min
            await pilot.pause()
            assert all(0 <= v <= 1 for v in waveform._data)

    @pytest.mark.asyncio
    async def test_data_clears_on_stop(self):
        """Data clears when recording stops."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget()

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            waveform.update_level(0.5)
            waveform.stop_recording()
            await pilot.pause()
            assert len(waveform._data) == 0


class TestWaveformWidgetMaxSamples:
    """Test WaveformWidget sample limit."""

    @pytest.mark.asyncio
    async def test_limits_samples(self):
        """Widget limits number of samples."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield WaveformWidget(max_samples=10)

        async with TestApp().run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            waveform.start_recording()
            for i in range(20):
                waveform.update_level(0.5)
            await pilot.pause()
            assert len(waveform._data) <= 10
