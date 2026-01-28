"""Main TUI application using Textual.

SOLID principles applied:
- Single Responsibility: TUIApp handles UI, WorkerController handles worker lifecycle.
- Dependency Inversion: WorkerController injected with callbacks.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
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
        Binding("escape", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
        Binding("h", "switch_tab('history-tab')", "History", show=False),
        Binding("s", "switch_tab('settings-tab')", "Settings", show=False),
        Binding("c", "copy_selected", "Copy", show=False),
    ]

    def __init__(self, test_mode: bool = False, config: Config | None = None):
        """Initialize TUI application.

        Args:
            test_mode: If True, skip starting worker (for testing).
            config: Optional config to use (for CLI flags like --debug).
        """
        super().__init__()
        self._test_mode = test_mode
        self._worker_controller = None
        self._status_bar = None
        self._waveform = None
        self._history_screen = None
        self._settings_screen = None
        self.config = config if config is not None else Config.load()
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

    def _is_hotkey_capture_active(self) -> bool:
        """Check if hotkey capture mode is active.

        Returns:
            True if any HotkeyCapture widget is in capture mode.
        """
        try:
            from soupawhisper.tui.widgets.hotkey_capture import HotkeyCapture

            widgets = self.query(HotkeyCapture)
            return any(w.is_capturing for w in widgets)
        except Exception:
            return False

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to specified tab.

        Args:
            tab_id: Tab ID to switch to (e.g., 'history-tab', 'settings-tab').
        """
        if self._is_hotkey_capture_active():
            return  # Block during hotkey capture

        tabs = self.query(TabbedContent)
        if tabs:
            tabs.first().active = tab_id

    def action_switch_to_history(self) -> None:
        """Switch to History tab."""
        self.action_switch_tab("history-tab")

    def action_switch_to_settings(self) -> None:
        """Switch to Settings tab."""
        self.action_switch_tab("settings-tab")

    def action_copy_selected(self) -> None:
        """Copy selected history entry to clipboard."""
        if self._is_hotkey_capture_active():
            return  # Block during hotkey capture

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

    def pause_hotkey_listener(self) -> None:
        """Pause hotkey listener (for hotkey capture mode)."""
        if hasattr(self, "_worker_controller") and self._worker_controller:
            self._worker_controller.pause()

    def resume_hotkey_listener(self) -> None:
        """Resume hotkey listener (after hotkey capture)."""
        if hasattr(self, "_worker_controller") and self._worker_controller:
            self._worker_controller.resume()

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
    """Run the TUI application.

    Checks terminal compatibility before starting.
    """
    import os
    import sys

    # Check terminal compatibility
    term = os.environ.get("TERM", "")
    if term in ("dumb", "", "unknown"):
        print("Error: TUI requires a terminal with escape sequence support.")
        print(f"Current TERM={term!r}")
        print()
        print("Solutions:")
        print("  1. Run from Terminal.app, iTerm2, or another full terminal")
        print("  2. Set TERM manually: TERM=xterm-256color uv run soupawhisper --gui")
        print()
        print("Note: IDE integrated terminals (Cursor, VS Code) may not work properly.")
        sys.exit(1)

    config = Config.load()
    app = TUIApp(config=config)
    app.run()
