"""Tests for application icon configuration.

TDD: These tests verify icon files exist and are properly configured.
"""

from pathlib import Path


class TestIconFiles:
    """Test that icon files exist in the correct locations."""

    def test_main_icon_exists(self):
        """Main microphone icon must exist in assets directory."""
        icon_path = Path("src/soupawhisper/gui/assets/microphone.png")
        assert icon_path.exists(), f"Main icon not found: {icon_path}"

    def test_recording_icon_exists(self):
        """Recording status icon must exist."""
        icon_path = Path("src/soupawhisper/gui/assets/microphone-recording.png")
        assert icon_path.exists(), f"Recording icon not found: {icon_path}"

    def test_processing_icon_exists(self):
        """Processing status icon must exist."""
        icon_path = Path("src/soupawhisper/gui/assets/microphone-processing.png")
        assert icon_path.exists(), f"Processing icon not found: {icon_path}"

    def test_icon_is_valid_png(self):
        """Icon must be a valid PNG image."""
        from PIL import Image
        icon_path = Path("src/soupawhisper/gui/assets/microphone.png")
        img = Image.open(icon_path)
        assert img.format == "PNG", f"Icon is not PNG: {img.format}"
        assert img.size[0] >= 16, "Icon too small"
        assert img.size[1] >= 16, "Icon too small"


class TestIconConfiguration:
    """Test that icons are properly configured in the application."""

    def test_assets_dir_exists(self):
        """Assets directory must exist."""
        assets_dir = Path("src/soupawhisper/gui/assets")
        assert assets_dir.exists(), f"Assets dir not found: {assets_dir}"
        assert assets_dir.is_dir(), f"Assets is not a directory: {assets_dir}"

    def test_icon_files_in_assets(self):
        """All required icons must exist in assets directory."""
        assets_dir = Path("src/soupawhisper/gui/assets")
        required = ["microphone.png", "microphone-recording.png", "microphone-processing.png"]
        for icon_name in required:
            icon_path = assets_dir / icon_name
            assert icon_path.exists(), f"Required icon not found: {icon_path}"


class TestDesktopEntry:
    """Test Linux desktop entry configuration for proper icon display."""

    def test_desktop_file_exists(self):
        """Desktop entry file must exist in data directory."""
        desktop_file = Path("data/soupawhisper.desktop")
        assert desktop_file.exists(), f"Desktop file not found: {desktop_file}"

    def test_desktop_file_has_icon(self):
        """Desktop entry must have Icon field."""
        desktop_file = Path("data/soupawhisper.desktop")
        content = desktop_file.read_text()
        assert "Icon=" in content, "Desktop file missing Icon field"

    def test_desktop_file_has_startup_wm_class(self):
        """Desktop entry must have StartupWMClass=flet for taskbar icon.
        
        On Linux, the taskbar icon is determined by matching WM_CLASS
        of the window with StartupWMClass in the .desktop file.
        Flet windows have WM_CLASS="flet", "Flet".
        """
        desktop_file = Path("data/soupawhisper.desktop")
        content = desktop_file.read_text()
        assert "StartupWMClass=flet" in content, (
            "Desktop file must have StartupWMClass=flet to show correct icon in taskbar. "
            "Flet windows have WM_CLASS='flet'."
        )

    def test_hicolor_icon_exists(self):
        """Icon must exist in data/icons for installation."""
        icon_path = Path("data/icons/soupawhisper.png")
        assert icon_path.exists(), f"Hicolor icon not found: {icon_path}"


class TestDockBadge:
    """Test that Dock badge is used for recording status."""

    def test_on_recording_sets_badge(self):
        """_on_recording should set page.window.badge_label."""
        from unittest.mock import MagicMock

        from soupawhisper.gui.app import GUIApp

        app = GUIApp()
        app.page = MagicMock()

        # Recording started
        app._on_recording(True)
        assert app.page.window.badge_label == "REC"

        # Recording stopped
        app._on_recording(False)
        assert app.page.window.badge_label == ""
