"""Main GUI application using Flet.

SOLID principles applied:
- Single Responsibility: GUIApp handles only UI, WorkerManager handles background work
- Dependency Inversion: WorkerManager injected with callbacks
"""

import atexit
from pathlib import Path
from typing import Optional

import flet as ft

from soupawhisper.config import CONFIG_PATH, Config
from soupawhisper.logging import get_logger
from soupawhisper.storage import HistoryStorage

from .base import send_ui_event
from .history_tab import HistoryTab
from .settings_tab import SettingsTab
from .worker import WorkerManager

log = get_logger()

# Global reference for atexit cleanup
_app_instance: Optional["GUIApp"] = None


class GUIApp:
    """Main GUI application controller.
    
    Responsibilities:
    - Setup and manage Flet page
    - Handle tab navigation
    - Coordinate between components
    
    Background work is delegated to WorkerManager.
    """

    def __init__(self):
        """Initialize GUI application."""
        global _app_instance
        _app_instance = self

        self.config = Config.load()
        self.history = HistoryStorage()
        self.page: Optional[ft.Page] = None
        self.history_tab: Optional[HistoryTab] = None
        self._worker: Optional[WorkerManager] = None

        # Register cleanup on exit
        atexit.register(self._cleanup)

    @property
    def core(self):
        """Get the core app instance (for backward compatibility)."""
        return self._worker.core if self._worker else None

    def main(self, page: ft.Page) -> None:
        """Flet main entry point.

        Args:
            page: Flet page instance
        """
        self.page = page
        self._setup_page()
        self._setup_tabs()
        self._start_worker()

    def _setup_page(self) -> None:
        """Configure page settings."""
        if not self.page:
            return

        self.page.title = "SoupaWhisper"
        self.page.window.width = 400
        self.page.window.height = 500
        self.page.window.min_width = 350
        self.page.window.min_height = 400
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0

        # Set window icon for title bar (absolute path required on Linux)
        icon_path = Path(__file__).parent / "assets" / "microphone.png"
        if icon_path.exists():
            self.page.window.icon = str(icon_path.absolute())

        # Handle cleanup when window closes
        self.page.on_disconnect = self._on_disconnect

        # Subscribe to UI events from background threads (thread-safe)
        self.page.pubsub.subscribe(self._handle_pubsub)

    def _setup_tabs(self) -> None:
        """Create tab layout with manual switching."""
        if not self.page:
            return

        self.history_tab = HistoryTab(
            history=self.history,
            on_copy=self._copy_to_clipboard,
            history_days=self.config.history_days,
        )

        self._settings_tab = SettingsTab(
            config=self.config,
            on_save=self._save_field,
        )

        # Content container that switches between tabs
        self._tab_content = ft.Container(
            content=self.history_tab,
            expand=True,
        )

        # Tab buttons
        self._history_btn = ft.TextButton(
            "History",
            style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
            on_click=lambda _: self._switch_tab(0),
        )
        self._settings_btn = ft.TextButton(
            "Settings",
            style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE_VARIANT),
            on_click=lambda _: self._switch_tab(1),
        )

        tab_bar = ft.Row(
            [self._history_btn, self._settings_btn],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page.add(
            ft.Column([
                ft.Container(tab_bar, padding=8),
                ft.Divider(height=1),
                self._tab_content,
            ], expand=True, spacing=0)
        )

    def _switch_tab(self, index: int) -> None:
        """Switch to specified tab."""
        if index == 0:
            self._tab_content.content = self.history_tab
            self._history_btn.style = ft.ButtonStyle(color=ft.Colors.PRIMARY)
            self._settings_btn.style = ft.ButtonStyle(color=ft.Colors.ON_SURFACE_VARIANT)
        else:
            self._tab_content.content = self._settings_tab
            self._history_btn.style = ft.ButtonStyle(color=ft.Colors.ON_SURFACE_VARIANT)
            self._settings_btn.style = ft.ButtonStyle(color=ft.Colors.PRIMARY)

        if self.page:
            self.page.update()

    def _start_worker(self) -> None:
        """Start background worker for hotkey listening."""
        if not self.page:
            return
            
        self._worker = WorkerManager(
            config=self.config,
            on_transcription=self._on_transcription,
            on_recording=self._on_recording,
            on_transcribing=self._on_transcribing,
            on_worker_done=self._cleanup,
        )
        self._worker.start(self.page.run_thread)

    def _on_recording(self, is_recording: bool) -> None:
        """Called when recording state changes.

        Args:
            is_recording: True if recording started, False if stopped
        """
        pass  # Status indicator removed (was tray icon)

    def _on_transcribing(self, is_transcribing: bool) -> None:
        """Called when transcription state changes.

        Args:
            is_transcribing: True if transcription started, False if completed
        """
        pass  # Status indicator removed (was tray icon)

    def _on_transcription(self, text: str, language: str) -> None:
        """Called when transcription completes (from background thread).

        Args:
            text: Transcribed text
            language: Detected language
        """
        # Save to history (safe in background thread)
        if self.config.history_enabled:
            self.history.add(text, language)
            self.history.delete_old(self.config.history_days)

        # Notify UI thread via pub/sub (thread-safe)
        send_ui_event(self.page, "transcription_complete")

    def _handle_pubsub(self, message: dict) -> None:
        """Handle pub/sub messages in UI thread.

        This is called by Flet in the UI thread, making it safe
        to update controls.

        Args:
            message: Message dict with "type" key
        """
        if message.get("type") == "transcription_complete":
            if self.history_tab:
                self.history_tab.refresh()
            if self.page:
                self.page.update()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard.

        Args:
            text: Text to copy
        """
        from soupawhisper.clipboard import copy_to_clipboard
        copy_to_clipboard(text)

    def _save_field(self, field_name: str, value: object) -> None:
        """Save a single config field.

        Args:
            field_name: Name of the config field
            value: New value for the field
        """
        # Update config
        setattr(self.config, field_name, value)
        self.config.save(CONFIG_PATH)

        # Update history tab if history_days changed
        if field_name == "history_days" and self.history_tab:
            self.history_tab.history_days = value
            self.history_tab.refresh()

    def _show_window(self) -> None:
        """Show main window."""
        if self.page:
            self.page.window.visible = True
            self.page.window.focused = True
            self.page.update()

    def _hide_window(self) -> None:
        """Hide main window."""
        if self.page:
            self.page.window.visible = False
            self.page.update()

    def _on_disconnect(self, e) -> None:
        """Handle page disconnect (window closed)."""
        log.info("Window closed, cleaning up...")
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._worker:
            self._worker.stop()

    def _quit(self) -> None:
        """Quit application."""
        log.info("Quitting application...")
        self._cleanup()
        if self.page:
            self.page.window.close()


def run_gui() -> None:
    """Run the GUI application."""
    app = GUIApp()
    assets_dir = Path(__file__).parent / "assets"
    ft.run(main=app.main, assets_dir=str(assets_dir))
