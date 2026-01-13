"""Base GUI utilities and mixins.

Provides common functionality for Flet components following DRY principle.
"""

import flet as ft


def get_page_safe(control: ft.Control) -> ft.Page | None:
    """Safely get the page from a control.
    
    Flet raises RuntimeError if control is not attached to a page.
    This function catches that and returns None.
    
    Args:
        control: The control to get page from
        
    Returns:
        The page or None if not attached
    """
    try:
        return control.page
    except RuntimeError:
        return None


def safe_update(page: ft.Page | None, control: ft.Control) -> None:
    """Safely update a control if attached to a page.
    
    Handles the case where page is None or control is not attached.
    Also handles Flet's RuntimeError when control has no page.
    
    Args:
        page: The page (can be None)
        control: The control to update
    """
    try:
        # page can be None, or accessing control.page can raise RuntimeError
        if page is not None:
            control.update()
    except RuntimeError:
        pass  # Control not attached to page yet


def safe_control_update(control: ft.Control) -> None:
    """Safely update a control, getting its page automatically.
    
    This is the recommended method when you have only the control.
    It handles all the edge cases of Flet's page property.
    
    Args:
        control: The control to update
    """
    page = get_page_safe(control)
    safe_update(page, control)


def show_snack(page: ft.Page | None, message: str, duration: int = 1000) -> None:
    """Show a snack bar notification.
    
    Args:
        page: The page to show snack on (can be None)
        message: Message to display
        duration: Duration in ms
    """
    try:
        if page is not None:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                duration=duration,
            )
            page.snack_bar.open = True
            page.update()
    except RuntimeError:
        pass  # Page closed or control not attached


def show_snack_on_control(control: ft.Control, message: str, duration: int = 1000) -> None:
    """Show a snack bar notification, getting page from control.
    
    Args:
        control: The control to get page from
        message: Message to display
        duration: Duration in ms
    """
    page = get_page_safe(control)
    show_snack(page, message, duration)


class SafeUpdateMixin:
    """Mixin providing safe update functionality for Flet components.
    
    Requires the component to have a `page` attribute.
    """
    
    page: ft.Page | None
    
    def _safe_update(self, control: ft.Control) -> None:
        """Safely update a control if attached to a page."""
        safe_update(self.page, control)
    
    def _show_snack(self, message: str, duration: int = 1000) -> None:
        """Show a snack bar notification."""
        show_snack(self.page, message, duration)
