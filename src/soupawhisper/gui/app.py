"""Main GUI application using Flet."""

import atexit
import threading
from pathlib import Path
from typing import Optional

import flet as ft

from soupawhisper.app import App
from soupawhisper.backend import create_backend
from soupawhisper.config import CONFIG_PATH, Config
from soupawhisper.logging import get_logger
from soupawhisper.storage import HistoryStorage

from .history_tab import HistoryTab
from .settings_tab import SettingsTab
from .tray import TrayIcon

log = get_logger()

# Global reference for atexit cleanup
_app_instance: Optional["GUIApp"] = None


class GUIApp:
    """Main GUI application controller."""

    def __init__(self):
        """Initialize GUI application."""
        global _app_instance
        _app_instance = self

        self.config = Config.load()
        self.history = HistoryStorage()
        self.core: Optional[App] = None
        self.tray: Optional[TrayIcon] = None
        self.page: Optional[ft.Page] = None
        self.history_tab: Optional[HistoryTab] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._running = True

        # Register cleanup on exit
        atexit.register(self._cleanup)

    def main(self, page: ft.Page) -> None:
        """Flet main entry point.

        Args:
            page: Flet page instance
        """
        self.page = page
        self._setup_page()
        self._setup_tabs()
        self._setup_tray()
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

        # Set window icon for taskbar
        icon_path = Path(__file__).parent / "assets" / "microphone.png"
        if icon_path.exists():
            self.page.window.icon = str(icon_path)

        # Handle cleanup when window closes
        self.page.on_disconnect = self._on_disconnect

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

    def _setup_tray(self) -> None:
        """Initialize system tray icon."""
        self.tray = TrayIcon(
            on_show=self._show_window,
            on_quit=self._quit,
        )
        self.tray.start()

    def _start_worker(self) -> None:
        """Start background worker for hotkey listening."""
        if self.page:
            self.page.run_thread(self._worker_loop)
            # Start monitor thread to detect window close
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def _monitor_loop(self) -> None:
        """Monitor Flet process and cleanup when closed.

        WORKAROUND: Flet doesn't reliably fire on_disconnect when the window
        is closed via the X button. This monitor thread polls for the Flet
        subprocess and triggers cleanup when it terminates.

        See: https://github.com/flet-dev/flet/issues/...
        TODO: Remove when Flet fixes window close detection.
        """
        import os
        import time

        # Wait for Flet to start
        time.sleep(2)

        while self._running:
            time.sleep(1)
            try:
                if not self._is_flet_running():
                    log.info("Flet process gone, cleaning up...")
                    self._cleanup()
                    os._exit(0)
            except Exception:
                pass

    def _is_flet_running(self) -> bool:
        """Check if Flet subprocess is still running.

        Returns:
            True if Flet process is running, False otherwise.
        """
        import subprocess
        import sys

        try:
            if sys.platform == "win32":
                # Windows: check for flet.exe in task list
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq flet.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return "flet.exe" in result.stdout
            else:
                # Linux/macOS: use pgrep
                result = subprocess.run(
                    ["pgrep", "-f", "flet/flet"],
                    capture_output=True,
                    timeout=5,
                )
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True  # Assume running if check fails

    def _worker_loop(self) -> None:
        """Background worker that runs the core app."""
        try:
            backend = create_backend(self.config.backend, self.config.typing_delay)
            self.core = App(
                config=self.config,
                backend=backend,
                on_transcription=self._on_transcription,
                on_recording=self._on_recording,
                on_transcribing=self._on_transcribing,
            )
            self.core.run()
        except Exception as e:
            log.error(f"Worker error: {e}")
        finally:
            # Worker finished, cleanup
            self._cleanup()

    def _on_recording(self, is_recording: bool) -> None:
        """Called when recording state changes.

        Args:
            is_recording: True if recording started, False if stopped
        """
        if self.tray:
            self.tray.set_status("recording" if is_recording else "ready")

    def _on_transcribing(self, is_transcribing: bool) -> None:
        """Called when transcription state changes.

        Args:
            is_transcribing: True if transcription started, False if completed
        """
        if self.tray:
            self.tray.set_status("transcribing" if is_transcribing else "ready")

    def _on_transcription(self, text: str, language: str) -> None:
        """Called when transcription completes.

        Args:
            text: Transcribed text
            language: Detected language
        """
        # Save to history
        if self.config.history_enabled:
            self.history.add(text, language)
            self.history.delete_old(self.config.history_days)

        # Refresh history tab (called from background thread)
        if self.history_tab and self.page:
            try:
                self.history_tab.refresh()
                self.page.update()  # Force UI update from background thread
            except Exception as e:
                log.warning(f"Failed to refresh history: {e}")

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
        """Hide main window to tray."""
        if self.page:
            self.page.window.visible = False
            self.page.update()

    def _on_disconnect(self, e) -> None:
        """Handle page disconnect (window closed)."""
        log.info("Window closed, cleaning up...")
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        self._running = False
        if self.core:
            self.core.stop()  # Stop hotkey listener
        if self.tray:
            self.tray.stop()

    def _quit(self) -> None:
        """Quit application (called from tray menu)."""
        log.info("Quitting application...")
        self._cleanup()
        if self.page:
            self.page.window.close()


def run_gui() -> None:
    """Run the GUI application."""
    app = GUIApp()
    ft.run(main=app.main)
