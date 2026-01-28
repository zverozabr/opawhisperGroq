"""Waveform visualization widget.

Uses Textual Sparkline for audio level display during recording.
KISS: Simple wrapper around Sparkline with recording state.

NOTE: Currently shows simulated waveform for visual feedback.
Real audio level monitoring would require:
- Streaming audio data (instead of file-based recording)
- Audio level analysis (RMS, peak detection)
"""

import random

from textual.reactive import reactive
from textual.widgets import Sparkline


class WaveformWidget(Sparkline):
    """Widget to display audio waveform during recording.

    Shows audio level as a sparkline visualization.
    Hidden when not recording.
    """

    DEFAULT_CSS = """
    WaveformWidget {
        height: 3;
        margin: 0 1;
        background: $surface;
    }

    WaveformWidget.-recording {
        background: $error-darken-2;
    }
    """

    is_visible = reactive(False)

    def __init__(self, max_samples: int = 50, **kwargs):
        """Initialize waveform widget.

        Args:
            max_samples: Maximum number of samples to display.
        """
        super().__init__(data=[], **kwargs)
        self._max_samples = max_samples
        self._data: list[float] = []
        self._is_recording = False

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.display = False  # Hidden by default

    def start_recording(self) -> None:
        """Start displaying waveform."""
        self._is_recording = True
        self._data = []
        self.data = []
        self.display = True
        self.is_visible = True
        self.add_class("-recording")
        # Start simulated waveform animation
        self._start_simulation()

    def stop_recording(self) -> None:
        """Stop displaying waveform."""
        self._is_recording = False
        self._data = []
        self.data = []
        self.display = False
        self.is_visible = False
        self.remove_class("-recording")
        # Stop simulation
        self._stop_simulation()

    def _start_simulation(self) -> None:
        """Start simulated waveform animation.

        KISS: Simulates audio levels for visual feedback.
        In future, can be replaced with real audio level monitoring.
        """
        self._simulation_timer = self.set_interval(0.1, self._simulate_level)

    def _stop_simulation(self) -> None:
        """Stop simulated waveform animation."""
        if hasattr(self, "_simulation_timer"):
            self._simulation_timer.stop()

    def _simulate_level(self) -> None:
        """Generate simulated audio level."""
        if self._is_recording:
            # Simulate varying audio levels
            level = 0.3 + random.random() * 0.5
            self.update_level(level)

    def update_level(self, level: float) -> None:
        """Update with new audio level.

        Args:
            level: Audio level (0.0 to 1.0).
        """
        if not self._is_recording:
            return

        # Normalize to 0-1 range
        normalized = max(0.0, min(1.0, level))
        self._data.append(normalized)

        # Limit samples
        if len(self._data) > self._max_samples:
            self._data = self._data[-self._max_samples :]

        # Update sparkline data
        self.data = self._data.copy()
