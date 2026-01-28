"""Main GUI application using Flet.

SOLID principles applied:
- Single Responsibility: GUIApp handles only UI, WorkerManager handles background work
- Dependency Inversion: WorkerManager injected with callbacks
"""

import atexit
import sys
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
        try:
            self.page = page
            self._preload_audio_devices()  # Cache audio devices for fast recording start
            self._log_permissions()  # Log permission status at startup
            self._setup_page()
            self._setup_tabs()
            self.page.update()  # Render UI before starting worker
            self._start_worker()
        except Exception as e:
            log.error(f"GUI init error: {e}")
            import traceback
            traceback.print_exc()

    def _preload_audio_devices(self) -> None:
        """Preload audio device cache for fast recording start."""
        from soupawhisper.audio import DeviceResolver

        DeviceResolver.refresh_cache()
        log.debug("Audio device cache refresh started")

    def _log_permissions(self) -> None:
        """Log macOS permission status at startup."""
        if sys.platform != "darwin":
            return

        from soupawhisper.backend.darwin import PermissionsHelper

        PermissionsHelper.log_status()

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

        # Permission status indicator (macOS only)
        permission_status = self._build_permission_status()
        self._permission_status_container = ft.Container(
            content=permission_status.content if hasattr(permission_status, "content") else permission_status,
            bgcolor=permission_status.bgcolor if hasattr(permission_status, "bgcolor") else None,
            padding=permission_status.padding if hasattr(permission_status, "padding") else None,
        )

        self.page.add(
            ft.Column([
                ft.Container(tab_bar, padding=8),
                self._permission_status_container,
                ft.Divider(height=1),
                self._tab_content,
            ], expand=True, spacing=0)
        )

    def _build_permission_status(self) -> ft.Control:
        """Build macOS permission status indicator.

        Uses PermissionsHelper (DRY) to check both Input Monitoring and Accessibility.
        """
        if sys.platform != "darwin":
            return ft.Container()

        from soupawhisper.backend.darwin import PermissionsHelper

        status = PermissionsHelper.check()

        if status.all_granted:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=14),
                    ft.Text("Permissions OK", size=12, color="green"),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                padding=4,
            )
        else:
            missing_text = ", ".join(status.missing)

            def open_settings(e):
                from soupawhisper.backend.darwin import open_accessibility_settings
                from soupawhisper.clipboard import copy_to_clipboard

                # Copy Python path to clipboard
                python_path = PermissionsHelper.get_python_path()
                copy_to_clipboard(python_path)

                # Open System Settings
                open_accessibility_settings()

                # Show instruction snackbar
                if self.page:
                    snack = ft.SnackBar(
                        content=ft.Text(
                            "Path copied! Click '+' → Cmd+Shift+G → Cmd+V → Go → Open",
                            color="white",
                        ),
                        bgcolor="orange",
                        duration=8000,
                        open=True,
                    )
                    self.page.overlay.append(snack)
                    self.page.update()

            def refresh_status(e):
                self._refresh_permission_status()

            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color="red", size=14),
                    ft.Text(f"Missing: {missing_text}", size=11, color="red"),
                    ft.TextButton(
                        "Fix",
                        style=ft.ButtonStyle(color="orange"),
                        on_click=open_settings,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_size=16,
                        tooltip="Check permissions again",
                        on_click=refresh_status,
                    ),
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                padding=4,
                bgcolor="#330000",
            )

    def _refresh_permission_status(self) -> None:
        """Refresh permission status indicator."""
        if sys.platform != "darwin" or not self.page:
            return

        # Rebuild status indicator
        new_status = self._build_permission_status()

        # Find and replace in page
        if hasattr(self, "_permission_status_container"):
            self._permission_status_container.content = new_status.content
            self._permission_status_container.bgcolor = new_status.bgcolor
            self.page.update()

            # If permissions OK now, restart worker
            from soupawhisper.backend.darwin import PermissionsHelper
            status = PermissionsHelper.check()
            if status.all_granted:
                log.info("All permissions granted - restarting worker")
                self._restart_worker()

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
        if self.page:
            # Show/hide badge on Dock icon
            self.page.window.badge_label = "REC" if is_recording else ""
            self.page.update()

    def _on_transcribing(self, is_transcribing: bool) -> None:
        """Called when transcription state changes.

        Args:
            is_transcribing: True if transcription started, False if completed
        """
        # Indicator already hidden when recording stopped
        # No additional indicator for transcribing (KISS)
        pass

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

        # Restart worker if hotkey, backend, or audio settings changed
        if field_name in ("hotkey", "backend", "typing_delay", "audio_device") and self._worker:
            log.info(f"Restarting worker due to {field_name} change")
            self._worker.stop()
            self._start_worker()

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
