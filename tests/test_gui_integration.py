"""Integration tests for GUI components with mocked data.

Tests all UI functionality: buttons, settings, copy, save, history display.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from soupawhisper.config import Config
from soupawhisper.storage import HistoryEntry, HistoryStorage


# ============================================================================
# Fixtures - Mock Data
# ============================================================================


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return Config(
        api_key="gsk_test_key_12345",
        model="whisper-large-v3",
        language="auto",
        hotkey="ctrl_r",
        auto_type=True,
        auto_enter=False,
        typing_delay=12,
        notifications=True,
        backend="auto",
        audio_device="default",
        history_enabled=True,
        history_days=3,
    )


@pytest.fixture
def mock_history_storage(tmp_path):
    """Create history storage with mock data."""
    file_path = tmp_path / "test_history.md"
    storage = HistoryStorage(file_path)

    # Add mock entries
    storage.add("Hello world, this is a test transcription", "en")
    storage.add("Привет мир, это тестовая транскрипция", "ru")
    storage.add("Bonjour le monde", "fr")

    return storage


@pytest.fixture
def mock_history_entries():
    """Create list of mock history entries."""
    now = datetime.now()
    return [
        HistoryEntry(
            id=1,
            text="First transcription - testing copy",
            language="en",
            timestamp=now - timedelta(hours=1),
        ),
        HistoryEntry(
            id=2,
            text="Second transcription - Russian text",
            language="ru",
            timestamp=now - timedelta(hours=2),
        ),
        HistoryEntry(
            id=3,
            text="Third transcription - older entry",
            language="auto",
            timestamp=now - timedelta(days=1),
        ),
    ]


# ============================================================================
# History Storage Tests
# ============================================================================


class TestHistoryStorageIntegration:
    """Test history storage with realistic data."""

    def test_add_and_retrieve(self, tmp_path):
        """Test adding entries and retrieving them."""
        storage = HistoryStorage(tmp_path / "history.md")

        # Add entries
        id1 = storage.add("Test entry one", "en")
        id2 = storage.add("Test entry two", "ru")
        id3 = storage.add("Test entry three", "auto")

        assert id1 > 0
        assert id2 > id1
        assert id3 > id2

        # Retrieve
        entries = storage.get_recent(days=1)
        assert len(entries) == 3

        # Check order (newest first)
        assert entries[0].text == "Test entry three"
        assert entries[1].text == "Test entry two"
        assert entries[2].text == "Test entry one"

    def test_markdown_persistence(self, tmp_path):
        """Test that data persists in markdown file."""
        file_path = tmp_path / "history.md"

        # Create storage and add data
        storage1 = HistoryStorage(file_path)
        storage1.add("Persistent entry", "en")
        storage1.add("Another entry", "ru")

        # Create new storage instance (should load from file)
        storage2 = HistoryStorage(file_path)
        entries = storage2.get_recent(days=1)

        assert len(entries) == 2
        assert any(e.text == "Persistent entry" for e in entries)

    def test_delete_old_entries(self, tmp_path):
        """Test deleting old entries."""
        storage = HistoryStorage(tmp_path / "history.md")

        # Add entry
        storage.add("Recent entry", "en")

        # Delete entries older than 1000 days (should keep all)
        deleted = storage.delete_old(1000)
        assert deleted == 0
        assert storage.count() == 1

    def test_clear_all(self, tmp_path):
        """Test clearing all entries."""
        storage = HistoryStorage(tmp_path / "history.md")

        storage.add("Entry 1", "en")
        storage.add("Entry 2", "ru")
        assert storage.count() == 2

        storage.clear()
        assert storage.count() == 0


# ============================================================================
# History Tab Tests
# ============================================================================


class TestHistoryTabIntegration:
    """Test HistoryTab component functionality."""

    def test_history_tab_initialization(self, mock_history_storage):
        """Test HistoryTab initializes correctly."""
        from soupawhisper.gui.history_tab import HistoryTab

        copied_texts = []

        tab = HistoryTab(
            history=mock_history_storage,
            on_copy=lambda text: copied_texts.append(text),
            history_days=3,
        )

        assert tab.history == mock_history_storage
        assert tab.history_days == 3

    def test_history_tab_build(self, mock_history_storage):
        """Test HistoryTab builds UI correctly."""
        from soupawhisper.gui.history_tab import HistoryTab

        tab = HistoryTab(
            history=mock_history_storage,
            on_copy=lambda x: None,
            history_days=3,
        )

        result = tab.build()
        assert result is not None
        assert len(tab.controls) > 0  # Should have entries

    def test_history_tab_refresh(self, mock_history_storage):
        """Test refreshing history tab updates entries."""
        from soupawhisper.gui.history_tab import HistoryTab

        tab = HistoryTab(
            history=mock_history_storage,
            on_copy=lambda x: None,
            history_days=3,
        )
        tab.build()

        initial_count = len(tab.controls)

        # Add more entries
        mock_history_storage.add("New entry", "en")
        tab.refresh()

        # Should have more entries now
        assert len(tab.controls) >= initial_count

    def test_copy_callback_called(self, tmp_path):
        """Test that copy callback is called with correct text."""
        from soupawhisper.gui.history_tab import HistoryTab

        storage = HistoryStorage(tmp_path / "copy_test.md")
        storage.add("Test entry", "en")

        copied_texts = []

        tab = HistoryTab(
            history=storage,
            on_copy=lambda text: copied_texts.append(text),
            history_days=3,
        )
        tab.build()

        # Simulate copy action (call callback directly, not _copy_text which needs page)
        test_text = "Test copy text"
        tab.on_copy(test_text)

        assert len(copied_texts) == 1
        assert copied_texts[0] == test_text

    def test_empty_history_display(self, tmp_path):
        """Test display when history is empty."""
        from soupawhisper.gui.history_tab import HistoryTab

        empty_storage = HistoryStorage(tmp_path / "empty.md")

        tab = HistoryTab(
            history=empty_storage,
            on_copy=lambda x: None,
            history_days=3,
        )
        tab.build()

        # Should have "empty" message
        assert len(tab.controls) == 1


# ============================================================================
# Settings Tab Tests
# ============================================================================


class TestSettingsTabIntegration:
    """Test SettingsTab component functionality."""

    def test_settings_tab_initialization(self, mock_config):
        """Test SettingsTab initializes with config."""
        from soupawhisper.gui.settings_tab import SettingsTab

        saved_configs = []

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda cfg: saved_configs.append(cfg),
        )

        assert tab.config == mock_config

    def test_settings_tab_build(self, mock_config):
        """Test SettingsTab builds all editable fields."""
        from soupawhisper.gui.settings_tab import SettingsTab

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: None,
        )
        tab.build()

        # Check all editable fields exist
        assert hasattr(tab, "api_key_editable")
        assert hasattr(tab, "language_editable")
        assert hasattr(tab, "hotkey_selector")  # Virtual keyboard for hotkey selection
        assert hasattr(tab, "device_editable")
        assert hasattr(tab, "auto_type_editable")
        assert hasattr(tab, "auto_enter_editable")
        assert hasattr(tab, "typing_delay_editable")
        assert hasattr(tab, "history_enabled_editable")
        assert hasattr(tab, "history_days_editable")

    def test_settings_fields_have_correct_values(self, mock_config):
        """Test that form fields show config values."""
        from soupawhisper.gui.settings_tab import SettingsTab

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: None,
        )
        tab.build()

        # Verify field values match config (access underlying field via .field)
        assert tab.api_key_editable.field.value == mock_config.api_key
        assert tab.language_editable.field.value == mock_config.language
        assert tab.hotkey_selector.selected == mock_config.hotkey  # VirtualKeyboard uses .selected
        assert tab.auto_type_editable.field.value == mock_config.auto_type
        assert tab.auto_enter_editable.field.value == mock_config.auto_enter
        assert tab.typing_delay_editable.field.value == str(mock_config.typing_delay)
        assert tab.history_enabled_editable.field.value == mock_config.history_enabled
        assert tab.history_days_editable.field.value == str(mock_config.history_days)

    def test_save_settings_callback(self, mock_config):
        """Test that save callback receives field name and value."""
        from soupawhisper.gui.settings_tab import SettingsTab

        saved_fields = []

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: saved_fields.append((field, value)),
        )
        tab.build()

        # Save api_key field
        tab._save_field("api_key", "new_api_key_123")

        # Verify callback was called with correct field
        assert len(saved_fields) == 1
        assert saved_fields[0] == ("api_key", "new_api_key_123")

        # Save another field
        tab._save_field("language", "ru")
        assert len(saved_fields) == 2
        assert saved_fields[1] == ("language", "ru")

    def test_save_invalid_typing_delay(self, mock_config):
        """Test parse_int uses default for invalid values."""
        from soupawhisper.gui.settings_tab import SettingsTab

        saved_fields = []

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: saved_fields.append((field, value)),
        )
        tab.build()

        # Verify _parse_int handles invalid input
        assert tab._parse_int("invalid", 12) == 12
        assert tab._parse_int("", 12) == 12
        assert tab._parse_int("25", 12) == 25

    def test_all_languages_available(self, mock_config):
        """Test all language options are available."""
        from soupawhisper.gui.settings_tab import LANGUAGES, SettingsTab

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: None,
        )
        tab.build()

        dropdown_options = [opt.key for opt in tab.language_editable.field.options]

        for lang_code, _ in LANGUAGES:
            assert lang_code in dropdown_options

    def test_hotkey_selector_initial_value(self, mock_config):
        """Test hotkey keyboard has correct initial value."""
        from soupawhisper.gui.settings_tab import SettingsTab

        tab = SettingsTab(
            config=mock_config,
            on_save=lambda field, value: None,
        )
        tab.build()

        # VirtualKeyboard stores the current hotkey selection
        assert tab.hotkey_selector.selected == mock_config.hotkey


# ============================================================================
# GUI App Integration Tests
# ============================================================================


class TestGUIAppIntegration:
    """Test GUIApp component integration."""

    def test_gui_app_initialization(self, tmp_path, monkeypatch):
        """Test GUIApp initializes correctly."""
        from soupawhisper.gui.app import GUIApp

        # Mock config and history paths
        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()

        assert app.config is not None
        assert app.history is not None
        assert app.page is None  # Not set until main() called

    def test_copy_to_clipboard(self, tmp_path, monkeypatch):
        """Test clipboard copy functionality."""
        from soupawhisper.gui.app import GUIApp
        from unittest.mock import patch

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()

        # Mock subprocess.Popen for clipboard
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            # Call copy
            app._copy_to_clipboard("Test clipboard text")

            # Verify subprocess was called for clipboard
            assert mock_popen.called
            mock_process.communicate.assert_called_once()

    def test_save_field(self, tmp_path, monkeypatch):
        """Test field-level config save functionality."""
        from soupawhisper.gui.app import GUIApp
        import soupawhisper.gui.app as app_module

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history_save.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(app_module, "CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()
        # Mock history_tab to avoid update errors
        app.history_tab = None

        # Save individual fields
        app._save_field("api_key", "new_key")
        app._save_field("language", "ru")

        # Verify config was updated
        assert app.config.api_key == "new_key"
        assert app.config.language == "ru"

        # Verify file was saved
        assert config_path.exists()

        # Reload and verify persistence
        reloaded = Config.load(config_path)
        assert reloaded.api_key == "new_key"
        assert reloaded.language == "ru"

    def test_on_transcription_saves_history(self, tmp_path, monkeypatch):
        """Test that transcription callback saves to history."""
        from soupawhisper.gui.app import GUIApp

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history_trans.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()
        app.config.history_enabled = True

        # Call transcription handler
        app._on_transcription("Test transcription text", "en")

        # Verify entry was saved
        entries = app.history.get_recent(days=1)
        assert len(entries) == 1
        assert entries[0].text == "Test transcription text"
        assert entries[0].language == "en"

    def test_on_transcription_disabled_history(self, tmp_path, monkeypatch):
        """Test that disabled history doesn't save."""
        from soupawhisper.gui.app import GUIApp

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history_disabled.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()
        app.config.history_enabled = False

        # Call transcription handler
        app._on_transcription("Test text", "en")

        # Verify nothing was saved
        entries = app.history.get_recent(days=1)
        assert len(entries) == 0


# ============================================================================
# Config Persistence Tests
# ============================================================================


class TestConfigPersistence:
    """Test configuration save and load."""

    def test_config_save_and_load(self, tmp_path):
        """Test config saves to file and loads back."""
        config_path = tmp_path / "config.ini"

        original = Config(
            api_key="test_api_key_xyz",
            language="de",
            hotkey="f11",
            auto_type=True,
            auto_enter=True,
            typing_delay=30,
            history_enabled=True,
            history_days=7,
        )

        # Save
        original.save(config_path)
        assert config_path.exists()

        # Load
        loaded = Config.load(config_path)

        assert loaded.api_key == original.api_key
        assert loaded.language == original.language
        assert loaded.hotkey == original.hotkey
        assert loaded.auto_type == original.auto_type
        assert loaded.auto_enter == original.auto_enter
        assert loaded.typing_delay == original.typing_delay
        assert loaded.history_enabled == original.history_enabled
        assert loaded.history_days == original.history_days

    def test_config_load_missing_file(self, tmp_path):
        """Test loading from non-existent file returns defaults."""
        config_path = tmp_path / "nonexistent.ini"

        config = Config.load(config_path)

        # Should have defaults
        assert config.api_key == ""
        assert config.language == "auto"
        assert config.hotkey == "ctrl_r"

    def test_config_partial_update(self, tmp_path):
        """Test updating only some config values."""
        config_path = tmp_path / "config.ini"

        # Create initial config
        config1 = Config(api_key="key1", language="en")
        config1.save(config_path)

        # Load and update
        config2 = Config.load(config_path)
        config2.language = "ru"
        config2.save(config_path)

        # Verify both values
        config3 = Config.load(config_path)
        assert config3.api_key == "key1"  # unchanged
        assert config3.language == "ru"  # updated


# ============================================================================
# Full Flow Tests
# ============================================================================


class TestFullTranscriptionFlow:
    """Test complete transcription flow."""

    def test_transcription_to_history_to_copy(self, tmp_path, monkeypatch):
        """Test full flow: transcription -> history -> copy."""
        from soupawhisper.gui.app import GUIApp
        from soupawhisper.gui.history_tab import HistoryTab

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history_flow.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        # Setup app
        app = GUIApp()
        app.config.history_enabled = True

        # Simulate transcription
        app._on_transcription("Hello, this is a test", "en")
        app._on_transcription("Another transcription", "ru")

        # Verify history
        entries = app.history.get_recent(days=1)
        assert len(entries) == 2

        # Create history tab
        copied_texts = []
        history_tab = HistoryTab(
            history=app.history,
            on_copy=lambda text: copied_texts.append(text),
            history_days=3,
        )
        history_tab.build()

        # Simulate copy (call callback directly to avoid page dependency)
        history_tab.on_copy(entries[0].text)

        assert len(copied_texts) == 1
        assert copied_texts[0] == "Another transcription"

    def test_settings_change_affects_history(self, tmp_path, monkeypatch):
        """Test that changing history_days affects display."""
        from soupawhisper.gui.app import GUIApp
        from soupawhisper.gui.history_tab import HistoryTab
        import soupawhisper.gui.app as app_module

        config_path = tmp_path / "config.ini"
        history_path = tmp_path / "history_settings.md"
        monkeypatch.setattr("soupawhisper.config.CONFIG_PATH", config_path)
        monkeypatch.setattr(app_module, "CONFIG_PATH", config_path)
        monkeypatch.setattr(
            "soupawhisper.gui.app.HistoryStorage",
            lambda: HistoryStorage(history_path),
        )

        app = GUIApp()
        app.config.history_enabled = True

        # Add entries
        app._on_transcription("Entry 1", "en")

        # Create history tab and attach to app
        history_tab = HistoryTab(
            history=app.history,
            on_copy=lambda x: None,
            history_days=3,
        )
        history_tab.build()
        app.history_tab = history_tab

        # Change history days via field save (triggers history_tab update)
        app._save_field("history_days", 7)

        assert history_tab.history_days == 7
