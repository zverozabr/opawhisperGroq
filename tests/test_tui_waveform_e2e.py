"""E2E tests for WaveformWidget integration.

TDD: Tests for waveform behavior in full application context.
"""

import pytest



class TestWaveformE2EIntegration:
    """E2E tests for waveform in TUIApp."""

    @pytest.mark.asyncio
    async def test_waveform_exists_in_app(self, tui_app_patched):
        """Waveform widget exists in TUIApp."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveforms = pilot.app.query(WaveformWidget)
            assert len(waveforms) == 1

    @pytest.mark.asyncio
    async def test_waveform_hidden_initially(self, tui_app_patched):
        """Waveform is hidden when app starts."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)
            assert not waveform.is_visible

    @pytest.mark.asyncio
    async def test_waveform_shows_on_recording(self, tui_app_patched):
        """Waveform appears when recording starts."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)

            # Simulate recording start
            pilot.app.on_recording_changed(True)
            await pilot.pause()

            assert waveform.is_visible

    @pytest.mark.asyncio
    async def test_waveform_hides_on_stop(self, tui_app_patched):
        """Waveform hides when recording stops."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)

            # Start then stop recording
            pilot.app.on_recording_changed(True)
            await pilot.pause()
            pilot.app.on_recording_changed(False)
            await pilot.pause()

            assert not waveform.is_visible

    @pytest.mark.asyncio
    async def test_waveform_animates_during_recording(self, tui_app_patched):
        """Waveform shows animation during recording."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)

            # Start recording
            pilot.app.on_recording_changed(True)
            await pilot.pause()

            # Wait for animation to add data
            import asyncio
            await asyncio.sleep(0.3)

            # Should have some data from simulation
            assert len(waveform._data) > 0

            # Stop recording
            pilot.app.on_recording_changed(False)


class TestWaveformE2EWorkflow:
    """E2E workflow tests for waveform."""

    @pytest.mark.asyncio
    async def test_full_recording_workflow_with_waveform(self, tui_app_patched):
        """Complete recording workflow shows/hides waveform correctly."""
        from soupawhisper.tui.widgets.waveform import WaveformWidget

        async with tui_app_patched.run_test() as pilot:
            waveform = pilot.app.query_one(WaveformWidget)

            # Initial state
            assert not waveform.is_visible

            # Start recording
            pilot.app.on_recording_changed(True)
            await pilot.pause()
            assert waveform.is_visible
            assert waveform._is_recording

            # Transcription starts (still recording)
            pilot.app.on_transcribing_changed(True)
            await pilot.pause()

            # Recording stops
            pilot.app.on_recording_changed(False)
            await pilot.pause()
            assert not waveform.is_visible
            assert not waveform._is_recording

            # Transcription completes
            pilot.app.on_transcribing_changed(False)
            await pilot.pause()

            # Waveform should still be hidden
            assert not waveform.is_visible
