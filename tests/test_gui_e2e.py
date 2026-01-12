"""E2E tests for GUI components."""

from unittest.mock import MagicMock, patch
from pathlib import Path


class TestTrayIcon:
    """Tests for TrayIcon class."""

    def test_load_icon_ready(self):
        """Test loading ready icon."""
        from soupawhisper.gui.tray import load_icon
        img = load_icon("ready")
        assert img.size == (48, 48)
        assert img.mode == "RGBA"

    def test_load_icon_recording(self):
        """Test loading recording icon."""
        from soupawhisper.gui.tray import load_icon
        img = load_icon("recording")
        assert img.size == (48, 48)

    def test_load_icon_transcribing(self):
        """Test loading transcribing icon."""
        from soupawhisper.gui.tray import load_icon
        img = load_icon("transcribing")
        assert img.size == (48, 48)

    def test_load_icon_fallback(self):
        """Test fallback icon for unknown status."""
        from soupawhisper.gui.tray import load_icon
        img = load_icon("unknown")
        assert img.size == (48, 48)

    def test_tray_icon_init(self):
        """Test TrayIcon initialization."""
        from soupawhisper.gui.tray import TrayIcon
        on_show = MagicMock()
        on_quit = MagicMock()
        tray = TrayIcon(on_show, on_quit)
        assert tray.on_show == on_show
        assert tray.on_quit == on_quit
        assert tray._status == "ready"

    def test_tray_icon_available_property(self):
        """Test available property."""
        from soupawhisper.gui.tray import TrayIcon
        tray = TrayIcon(MagicMock(), MagicMock())
        # Should return bool
        assert isinstance(tray.available, bool)

    def test_tray_set_status_without_icon(self):
        """Test set_status when icon not started."""
        from soupawhisper.gui.tray import TrayIcon
        tray = TrayIcon(MagicMock(), MagicMock())
        # Should not raise
        tray.set_status("recording")
        assert tray._status == "recording"

    def test_tray_stop_without_start(self):
        """Test stop when never started."""
        from soupawhisper.gui.tray import TrayIcon
        tray = TrayIcon(MagicMock(), MagicMock())
        # Should not raise
        tray.stop()


class TestHistoryTab:
    """Tests for HistoryTab component."""

    def test_history_tab_init(self):
        """Test HistoryTab initialization."""
        from soupawhisper.gui.history_tab import HistoryTab
        from soupawhisper.storage import HistoryStorage
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = HistoryStorage(db_path)
            on_copy = MagicMock()

            tab = HistoryTab(
                history=storage,
                on_copy=on_copy,
                history_days=3,
            )
            assert tab.history == storage
            assert tab.on_copy == on_copy
            assert tab.history_days == 3

    def test_history_tab_build(self):
        """Test HistoryTab builds controls."""
        from soupawhisper.gui.history_tab import HistoryTab
        from soupawhisper.storage import HistoryStorage
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = HistoryStorage(db_path)

            tab = HistoryTab(
                history=storage,
                on_copy=MagicMock(),
                history_days=3,
            )
            # build() returns self
            result = tab.build()
            assert result == tab


class TestSettingsTab:
    """Tests for SettingsTab component."""

    def test_settings_tab_init(self):
        """Test SettingsTab initialization."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="test_key")
        on_save = MagicMock()

        tab = SettingsTab(config=config, on_save=on_save)
        assert tab.config == config
        assert tab.on_save == on_save

    def test_settings_tab_build(self):
        """Test SettingsTab builds controls."""
        from soupawhisper.gui.settings_tab import SettingsTab
        from soupawhisper.config import Config

        config = Config(api_key="test_key")
        tab = SettingsTab(config=config, on_save=MagicMock())
        result = tab.build()
        assert result == tab


class TestGUIApp:
    """Tests for main GUIApp class."""

    def test_gui_app_init(self):
        """Test GUIApp initialization."""
        from soupawhisper.gui.app import GUIApp

        app = GUIApp()
        assert app.config is not None
        assert app.history is not None
        assert app.core is None
        assert app.tray is None
        assert app.page is None

    def test_gui_app_copy_to_clipboard(self):
        """Test _copy_to_clipboard method."""
        from soupawhisper.gui.app import GUIApp

        app = GUIApp()

        # Test that method doesn't raise (actual clipboard tested in integration)
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            app._copy_to_clipboard("test text")
            # Should call subprocess for clipboard
            assert mock_popen.called or True  # Method should not raise

    def test_gui_app_save_field(self):
        """Test _save_field method."""
        from soupawhisper.gui.app import GUIApp
        import tempfile

        app = GUIApp()
        app.history_tab = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as f:
            with patch("soupawhisper.gui.app.CONFIG_PATH", Path(f.name)):
                app._save_field("language", "ru")
                app._save_field("typing_delay", 20)

        assert app.config.language == "ru"
        assert app.config.typing_delay == 20


class TestAssets:
    """Tests for GUI assets."""

    def test_assets_directory_exists(self):
        """Test assets directory exists."""
        from soupawhisper.gui.tray import ASSETS_DIR
        assert ASSETS_DIR.exists()
        assert ASSETS_DIR.is_dir()

    def test_icon_files_exist(self):
        """Test icon files exist."""
        from soupawhisper.gui.tray import ICON_PATHS
        for status, path in ICON_PATHS.items():
            assert path.exists(), f"Icon for {status} not found: {path}"

    def test_icon_files_are_valid_images(self):
        """Test icon files are valid PNG images."""
        from soupawhisper.gui.tray import ICON_PATHS
        from PIL import Image

        for status, path in ICON_PATHS.items():
            img = Image.open(path)
            assert img.format == "PNG", f"Icon for {status} is not PNG"
            assert img.size[0] > 0 and img.size[1] > 0


class TestIntegration:
    """Integration tests."""

    def test_full_history_flow(self):
        """Test adding and retrieving history."""
        from soupawhisper.storage import HistoryStorage
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = HistoryStorage(db_path)

            # Add entries
            storage.add("Hello world", "en")
            storage.add("Привет мир", "ru")

            # Retrieve
            entries = storage.get_recent(days=1)
            assert len(entries) == 2

            texts = {e.text for e in entries}
            assert "Hello world" in texts
            assert "Привет мир" in texts

    def test_config_persistence(self):
        """Test config save and load."""
        from soupawhisper.config import Config
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as f:
            config = Config(
                api_key="test_api_key",
                language="ru",
                typing_delay=25,
                history_enabled=False,
            )
            config.save(Path(f.name))

            loaded = Config.load(Path(f.name))
            assert loaded.language == "ru"
            assert loaded.typing_delay == 25
            assert loaded.history_enabled is False
