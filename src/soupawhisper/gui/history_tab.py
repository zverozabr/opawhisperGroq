"""History tab component."""

from typing import Callable

import flet as ft

from soupawhisper.storage import HistoryEntry, HistoryStorage


class HistoryTab(ft.Column):
    """Tab displaying transcription history with copy buttons."""

    def __init__(
        self,
        history: HistoryStorage,
        on_copy: Callable[[str], None],
        history_days: int = 3,
    ):
        """Initialize history tab.

        Args:
            history: HistoryStorage instance
            on_copy: Callback when copy button clicked
            history_days: Number of days to show
        """
        super().__init__()
        self.history = history
        self.on_copy = on_copy
        self.history_days = history_days
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    def build(self) -> ft.Column:
        """Build the history list."""
        self.refresh()
        return self

    def refresh(self) -> None:
        """Refresh history entries from database."""
        entries = self.history.get_recent(self.history_days)
        self.controls.clear()

        if not entries:
            self.controls.append(
                ft.Container(
                    content=ft.Text(
                        "History is empty",
                        color=ft.Colors.GREY_500,
                        size=14,
                    ),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for entry in entries:
                self.controls.append(self._create_entry_card(entry))

        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass  # Not added to page yet

    def _create_entry_card(self, entry: HistoryEntry) -> ft.Container:
        """Create a card for a single history entry."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                entry.text,
                                size=14,
                                max_lines=3,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{entry.time_str}, {entry.language or 'auto'}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=20,
                        tooltip="Copy",
                        on_click=lambda e, text=entry.text: self._copy_text(text),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_800)),
        )

    def _copy_text(self, text: str) -> None:
        """Copy text and show feedback."""
        self.on_copy(text)
        try:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Copied"),
                    duration=1000,
                )
                self.page.snack_bar.open = True
                self.page.update()
        except RuntimeError:
            pass  # Control not attached to page yet
