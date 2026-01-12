"""Tests for application icon configuration.

TDD: These tests verify icon files exist and are properly configured.
"""

from pathlib import Path
import pytest


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

    def test_tray_icon_paths_valid(self):
        """Tray icon paths in tray.py must point to existing files."""
        from soupawhisper.gui.tray import ICON_PATHS
        for status, path in ICON_PATHS.items():
            assert path.exists(), f"Tray icon for '{status}' not found: {path}"

    def test_tray_load_icon_returns_image(self):
        """load_icon function must return a valid PIL Image."""
        from soupawhisper.gui.tray import load_icon
        from PIL import Image
        for status in ["ready", "recording", "transcribing"]:
            img = load_icon(status)
            assert isinstance(img, Image.Image), f"load_icon({status}) didn't return Image"
            assert img.size[0] > 0, f"load_icon({status}) returned empty image"
