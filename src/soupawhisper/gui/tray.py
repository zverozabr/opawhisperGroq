"""System tray icon using pystray (optional)."""

from pathlib import Path
from typing import Callable

from PIL import Image

from soupawhisper.logging import get_logger

log = get_logger()


ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATHS = {
    "ready": ASSETS_DIR / "microphone.png",
    "recording": ASSETS_DIR / "microphone-recording.png",
    "transcribing": ASSETS_DIR / "microphone-processing.png",
}


def load_icon(status: str = "ready") -> Image.Image:
    """Load tray icon for given status."""
    path = ICON_PATHS.get(status, ICON_PATHS["ready"])
    if path.exists():
        return Image.open(path)
    # Fallback
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    colors = {"ready": "#4CAF50", "recording": "#F44336", "transcribing": "#2196F3"}
    draw.ellipse([4, 4, 44, 44], fill=colors.get(status, "#4CAF50"))
    return img


def _check_tray_available() -> bool:
    """Check if system tray is available."""
    import importlib.util
    import sys

    # Check if pystray is installed
    if importlib.util.find_spec("pystray") is None:
        return False

    if sys.platform == "darwin":
        return True  # macOS always has tray support
    elif sys.platform == "win32":
        return True  # Windows always has tray support
    else:
        # Linux - try GTK/AppIndicator first, fallback to xorg
        if importlib.util.find_spec("gi") is not None:
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                return True
            except (ImportError, ValueError):
                pass
        # Try xorg backend (X11)
        if importlib.util.find_spec("pystray._xorg") is not None:
            return True
        return False


class TrayIcon:
    """System tray icon manager (gracefully handles unavailable tray)."""

    def __init__(self, on_show: Callable[[], None], on_quit: Callable[[], None]):
        self.on_show = on_show
        self.on_quit = on_quit
        self._icon = None
        self._status = "ready"
        self._available = _check_tray_available()

    @property
    def available(self) -> bool:
        """Return True if tray is available."""
        return self._available

    def start(self) -> None:
        """Start tray icon (no-op if unavailable)."""
        if not self._available:
            log.warning("System tray not available")
            return
        try:
            import pystray
            log.info("Starting tray icon...")
            menu = pystray.Menu(
                pystray.MenuItem("Открыть", self._show_window, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Выход", self._quit),
            )
            self._icon = pystray.Icon(
                name="soupawhisper",
                icon=load_icon("ready"),
                title="SoupaWhisper",
                menu=menu,
            )
            log.info("Tray icon created, running detached")
            self._icon.run_detached()
            log.info("Tray icon started")
        except Exception as e:
            log.error(f"Tray error: {e}", exc_info=True)
            self._available = False

    def stop(self) -> None:
        """Stop tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def set_status(self, status: str) -> None:
        """Update tray icon status."""
        if self._status == status:
            return  # No change
        log.debug(f"Tray status: {self._status} -> {status}")
        self._status = status
        if self._icon:
            try:
                self._icon.icon = load_icon(status)
                self._icon.title = f"SoupaWhisper - {status}"
            except Exception as e:
                log.warning(f"Failed to update tray icon: {e}")

    def _show_window(self, icon, item) -> None:
        self.on_show()

    def _quit(self, icon, item) -> None:
        self.stop()
        self.on_quit()
