"""Main TUI application using Textual.

SOLID principles applied:
- Single Responsibility: TUIApp handles UI, WorkerController handles worker lifecycle.
- Dependency Inversion: WorkerController injected with callbacks.
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

from soupawhisper.config import CONFIG_PATH, Config
from soupawhisper.logging import get_logger
from soupawhisper.storage import HistoryStorage
from soupawhisper.tui.screens.history import HistoryScreen
from soupawhisper.tui.screens.settings import SettingsScreen
from soupawhisper.tui.widgets.status_bar import StatusBar
from soupawhisper.tui.widgets.waveform import WaveformWidget
from soupawhisper.tui.worker_controller import WorkerController

log = get_logger()


class TUIApp(App):
    """Main TUI application controller.

    Responsibilities:
    - Setup and manage Textual app
    - Handle tab navigation
    - Coordinate between components

    Background work is delegated to WorkerManager.
    """

    TITLE = "SoupaWhisper"
    SUB_TITLE = "Voice Dictation"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "switch_to_history", "History"),
        ("s", "switch_to_settings", "Settings"),
        ("c", "copy_selected", "Copy"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self, test_mode: bool = False):
        """Initialize TUI application.

        Args:
            test_mode: If True, skip starting worker (for testing).
        """
        super().__init__()
        self._test_mode = test_mode
        self._worker_controller = None
        self._status_bar = None
        self._waveform = None
        self._history_screen = None
        self._settings_screen = None
        self.config = Config.load()
        self.history = HistoryStorage()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        self._status_bar = StatusBar(hotkey=self._format_hotkey())
        yield self._status_bar

        # Waveform visualization (shows during recording)
        self._waveform = WaveformWidget()
        yield self._waveform

        self._history_screen = HistoryScreen(
            history_storage=self.history,
            history_days=self.config.history_days,
        )
        self._settings_screen = SettingsScreen(
            config=self.config,
            on_save=self._save_field,
        )

        with TabbedContent(initial="history-tab"):
            with TabPane("History", id="history-tab"):
                yield self._history_screen
            with TabPane("Settings", id="settings-tab"):
                yield self._settings_screen
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted - start background worker."""
        # Skip worker in test mode (when run_test() is used)
        if not getattr(self, "_test_mode", False):
            self._start_worker()

    def _start_worker(self) -> None:
        """Start background worker for hotkey listening.

        SRP: Worker lifecycle delegated to WorkerController.
        """
        self._worker_controller = WorkerController(
            config=self.config,
            call_from_thread=self.call_from_thread,
            on_recording=self.on_recording_changed,
            on_transcribing=self.on_transcribing_changed,
            on_transcription=self.on_transcription_complete,
            on_error=self.on_error,
        )
        self._worker_controller.start()

    def _format_hotkey(self) -> str:
        """Format hotkey for display."""
        # Convert config hotkey (e.g., "ctrl_r") to display format
        hotkey = self.config.hotkey
        return hotkey.replace("_", "+").replace("ctrl", "Ctrl").replace("alt", "Alt")

    def action_quit(self) -> None:
        """Quit the application."""
        if self._worker_controller:
            self._worker_controller.stop()
        self.exit()

    def action_switch_to_history(self) -> None:
        """Switch to History tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "history-tab"

    def action_switch_to_settings(self) -> None:
        """Switch to Settings tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "settings-tab"

    def action_copy_selected(self) -> None:
        """Copy selected history entry to clipboard."""
        if self._history_screen:
            self._history_screen.copy_selected()

    def action_show_help(self) -> None:
        """Show help screen."""
        # Placeholder - will be implemented later
        pass

    def _save_field(self, field_name: str, value: object) -> None:
        """Save a single config field.

        Args:
            field_name: Name of the config field.
            value: New value.
        """
        setattr(self.config, field_name, value)
        self.config.save(CONFIG_PATH)

        # Restart worker if critical settings changed
        if field_name in ("hotkey", "backend", "typing_delay", "audio_device"):
            log.info(f"Restarting worker due to {field_name} change")
            self._restart_worker()

        # Update hotkey display in status bar
        if field_name == "hotkey" and self._status_bar:
            self._status_bar.hotkey = self._format_hotkey()

    def _restart_worker(self) -> None:
        """Restart the background worker."""
        if hasattr(self, "_worker_controller") and self._worker_controller:
            self._worker_controller.restart()

    # UI Event handlers (called from WorkerManager)
    def on_recording_changed(self, is_recording: bool) -> None:
        """Handle recording state change.

        Args:
            is_recording: True if recording started.
        """
        if self._status_bar:
            self._status_bar.is_recording = is_recording

        # Update waveform visualization
        if self._waveform:
            if is_recording:
                self._waveform.start_recording()
            else:
                self._waveform.stop_recording()

    def on_transcribing_changed(self, is_transcribing: bool) -> None:
        """Handle transcription state change.

        Args:
            is_transcribing: True if transcription started.
        """
        if self._status_bar:
            self._status_bar.is_transcribing = is_transcribing

    def on_transcription_complete(self, text: str, language: str) -> None:
        """Handle transcription completion.

        Args:
            text: Transcribed text.
            language: Detected language.
        """
        # Save to history and refresh display
        if self.config.history_enabled:
            self.history.add(text, language)
            self.history.delete_old(self.config.history_days)

        if self._history_screen:
            self._history_screen.refresh_data()

    def on_error(self, message: str) -> None:
        """Handle error.

        Args:
            message: Error message.
        """
        if self._status_bar:
            self._status_bar.error_message = message


def run_tui() -> None:
    """Run the TUI application."""
    app = TUIApp()
    app.run()
