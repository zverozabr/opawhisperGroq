"""Status bar widget for recording/transcription state.

Single Responsibility: Display current application state.
"""

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing recording and transcription state.

    States:
    - Ready: Waiting for hotkey
    - Recording: Microphone active (red background)
    - Transcribing: Processing audio
    - Error: Permission or other error

    Attributes:
        is_recording: True when recording audio.
        is_transcribing: True when transcription in progress.
        error_message: Error message to display (empty = no error).
        hotkey: Hotkey hint to display.
    """

    # Reactive properties trigger re-render and CSS class updates
    is_recording: reactive[bool] = reactive(False)
    is_transcribing: reactive[bool] = reactive(False)
    error_message: reactive[str] = reactive("")
    hotkey: str = "Ctrl+R"

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        width: 100%;
        height: 1;
        background: $surface;
        color: $text-muted;
        text-align: center;
    }

    StatusBar.recording {
        background: $error;
        color: $text;
    }

    StatusBar.transcribing {
        background: $warning;
        color: $text;
    }

    StatusBar.error {
        background: $error-darken-2;
        color: $error;
    }
    """

    def __init__(self, hotkey: str = "Ctrl+R", **kwargs):
        """Initialize status bar.

        Args:
            hotkey: Hotkey string to display as hint.
        """
        super().__init__(**kwargs)
        self.hotkey = hotkey

    def render(self) -> str:
        """Render status bar content based on current state."""
        if self.error_message:
            return f"⚠ {self.error_message}"

        if self.is_recording:
            return f"● REC  Recording...  Release {self.hotkey} to stop"

        if self.is_transcribing:
            return "◐ Transcribing...  Please wait"

        return f"○ Ready  Press {self.hotkey} to record"

    def watch_is_recording(self, is_recording: bool) -> None:
        """Update CSS class when recording state changes."""
        if is_recording:
            self.add_class("recording")
            self.remove_class("transcribing")
            self.remove_class("error")
        else:
            self.remove_class("recording")

    def watch_is_transcribing(self, is_transcribing: bool) -> None:
        """Update CSS class when transcribing state changes."""
        if is_transcribing:
            self.add_class("transcribing")
            self.remove_class("recording")
            self.remove_class("error")
        else:
            self.remove_class("transcribing")

    def watch_error_message(self, error_message: str) -> None:
        """Update CSS class when error state changes."""
        if error_message:
            self.add_class("error")
            self.remove_class("recording")
            self.remove_class("transcribing")
        else:
            self.remove_class("error")
