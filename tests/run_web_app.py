#!/usr/bin/env python3
"""Run SoupaWhisper GUI in web mode for E2E testing.

This version disables tray and worker to avoid blocking in headless mode.
"""

import uvicorn
import flet as ft

from soupawhisper.config import Config
from soupawhisper.storage import HistoryStorage
from soupawhisper.gui.history_tab import HistoryTab
from soupawhisper.gui.settings_tab import SettingsTab


class TestGUIApp:
    """Simplified GUI app for testing (no tray, no worker)."""

    def __init__(self):
        self.config = Config.load()
        self.history = HistoryStorage()
        self.page = None
        self.history_tab = None
        self._settings_tab = None

    def main(self, page: ft.Page) -> None:
        """Flet main entry point."""
        self.page = page
        self._setup_page()
        self._setup_tabs()

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

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from soupawhisper.clipboard import copy_to_clipboard
        copy_to_clipboard(text)

    def _save_field(self, field_name: str, value: object) -> None:
        """Save a single config field."""
        from soupawhisper.config import CONFIG_PATH
        setattr(self.config, field_name, value)
        self.config.save(CONFIG_PATH)

        # Update history tab if history_days changed
        if field_name == "history_days" and self.history_tab:
            self.history_tab.history_days = value
            self.history_tab.refresh()


def main():
    """Run app as ASGI web server on port 8550."""
    app = TestGUIApp()

    # Export as ASGI app
    asgi_app = ft.run(
        main=app.main,
        export_asgi_app=True,
    )

    # Run with uvicorn
    uvicorn.run(asgi_app, host="127.0.0.1", port=8550, log_level="warning")


if __name__ == "__main__":
    main()
