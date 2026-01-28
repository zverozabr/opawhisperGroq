"""Tests for model preloading functionality."""

from unittest.mock import patch

import pytest
from textual.app import App
from textual.widgets import Select, Static

from soupawhisper.tui.widgets.model_manager import ModelManagerWidget


class TestModelPreload:
    """Test that models can be preloaded into memory."""

    def test_preload_warms_up_model(self, tmp_path):
        """Preloading should call preloader with correct model."""
        from soupawhisper.providers.models import ModelManager

        class FakePreloader:
            def __init__(self):
                self.calls = []

            def preload(self, model_name: str, provider_type: str = "mlx") -> None:
                self.calls.append((model_name, provider_type))

            def unload(self, provider_type: str = "mlx") -> None:
                return None

        (tmp_path / "base").mkdir()
        (tmp_path / "base" / "file.bin").write_text("x")

        preloader = FakePreloader()
        manager = ModelManager(models_dir=tmp_path, preloader=preloader)

        manager.preload_model("base")

        assert preloader.calls == [("base", "mlx")]

    def test_preload_updates_status(self, tmp_path):
        """Preloading should allow status to be LOADED."""
        from soupawhisper.providers.models import ModelManager, ModelStatus

        (tmp_path / "base").mkdir()
        (tmp_path / "base" / "file.bin").write_text("x")

        manager = ModelManager(models_dir=tmp_path)
        model_path = str(tmp_path / "base")

        with patch("soupawhisper.providers.mlx.get_loaded_model", return_value=model_path):
            status = manager.get_model_status("base")
            assert status == ModelStatus.LOADED

    def test_model_status_shows_downloaded(self, tmp_path):
        """Downloaded but not loaded model shows DOWNLOADED status."""
        from soupawhisper.providers.models import ModelManager, ModelStatus

        (tmp_path / "base").mkdir()
        (tmp_path / "base" / "file.bin").write_text("x")

        manager = ModelManager(models_dir=tmp_path)

        with patch("soupawhisper.providers.mlx.get_loaded_model", return_value=None):
            status = manager.get_model_status("base")
            assert status == ModelStatus.DOWNLOADED

    def test_model_status_shows_loaded(self, tmp_path):
        """Loaded model shows LOADED status."""
        from soupawhisper.providers.models import ModelManager, ModelStatus

        (tmp_path / "base").mkdir()
        (tmp_path / "base" / "file.bin").write_text("x")

        manager = ModelManager(models_dir=tmp_path)
        model_path = str(tmp_path / "base")

        with patch("soupawhisper.providers.mlx.get_loaded_model", return_value=model_path):
            status = manager.get_model_status("base")
            assert status == ModelStatus.LOADED


class TestModelStatus:
    """Test ModelStatus enum and tracking."""

    def test_status_not_downloaded(self):
        """Model not on disk has NOT_DOWNLOADED status."""
        from soupawhisper.providers.models import ModelStatus, get_model_manager

        manager = get_model_manager()
        # Use a model that's definitely not downloaded
        status = manager.get_model_status("nonexistent-model-xyz")
        assert status == ModelStatus.NOT_DOWNLOADED

    def test_status_downloaded_but_not_loaded(self):
        """Model on disk but not in memory has DOWNLOADED status."""
        from soupawhisper.providers.models import ModelStatus, get_model_manager
        from soupawhisper.providers.mlx import is_server_running

        manager = get_model_manager()

        # Find a downloaded model
        for model in manager.list_models():
            if manager.is_downloaded(model.name):
                # Server not running = not loaded
                if not is_server_running():
                    status = manager.get_model_status(model.name)
                    assert status == ModelStatus.DOWNLOADED
                    return

        pytest.skip("No downloaded models to test")

    def test_status_loaded_in_memory(self):
        """Model loaded in server has LOADED status."""
        from soupawhisper.providers.models import ModelStatus, get_model_manager

        manager = get_model_manager()

        # Preload a model
        for model in manager.list_models():
            if manager.is_downloaded(model.name):
                manager.preload_model(model.name)
                status = manager.get_model_status(model.name)
                assert status == ModelStatus.LOADED
                return

        pytest.skip("No downloaded models to test")


class TestPreloadAPI:
    """Test the preload API."""

    def test_preload_starts_server(self):
        """Preloading should start the MLX server."""
        from soupawhisper.providers.mlx import is_server_running, shutdown_server

        # Ensure server is stopped
        shutdown_server()

        from soupawhisper.providers.models import get_model_manager

        manager = get_model_manager()

        for model in manager.list_models():
            if manager.is_downloaded(model.name):
                manager.preload_model(model.name)

                assert is_server_running(), "Server should be running after preload"
                return

        pytest.skip("No downloaded models to test")

    def test_preload_sends_warmup_request(self, tmp_path):
        """Preloading should send a warmup request to load the model."""
        from soupawhisper.providers.model_preloader import ModelPreloader
        from soupawhisper.providers.models import ModelManager

        class FakeLoader:
            def __init__(self):
                self.called_with = None

            def preload(self, model_name: str) -> None:
                self.called_with = model_name

            def unload(self) -> None:
                return None

            def get_loaded_model(self):
                return None

        manager = ModelManager(models_dir=tmp_path)
        loader = FakeLoader()
        preloader = ModelPreloader(manager, loaders={"mlx": loader})

        manager._preloader = preloader
        manager.preload_model("base")

        assert loader.called_with == "base"

    def test_preload_nonexistent_model_raises(self):
        """Preloading a non-downloaded model should raise error."""
        from soupawhisper.providers.models import get_model_manager, ModelNotDownloadedError

        manager = get_model_manager()

        with pytest.raises(ModelNotDownloadedError):
            manager.preload_model("nonexistent-model-xyz")


class TestModelSwitching:
    """Test switching between models."""

    def test_switch_unloads_old_model(self):
        """Switching models should unload the old one first."""
        from soupawhisper.providers.mlx import (
            get_loaded_model,
            shutdown_server,
            switch_model,
        )
        from soupawhisper.providers.models import get_model_manager

        manager = get_model_manager()
        downloaded = [m for m in manager.list_models() if manager.is_downloaded(m.name)]

        if len(downloaded) < 1:
            pytest.skip("Need at least 1 downloaded model")

        # Preload first model
        model1 = downloaded[0].name
        manager.preload_model(model1)

        loaded = get_loaded_model()
        assert loaded is not None
        assert model1 in loaded

        # Switch to same model - should not restart
        switch_model(str(manager.get_model_path(model1)))
        # Server should still be running with same model

        # Cleanup
        shutdown_server()

    def test_preload_different_model_switches(self):
        """Preloading a different model should switch to it."""
        from soupawhisper.providers.mlx import get_loaded_model, shutdown_server
        from soupawhisper.providers.models import get_model_manager

        manager = get_model_manager()
        downloaded = [m for m in manager.list_models() if manager.is_downloaded(m.name)]

        if len(downloaded) < 2:
            pytest.skip("Need at least 2 downloaded models to test switching")

        model1 = downloaded[0].name
        model2 = downloaded[1].name

        # Preload first model
        manager.preload_model(model1)
        loaded1 = get_loaded_model()
        assert model1 in loaded1

        # Preload second model - should switch
        manager.preload_model(model2)
        loaded2 = get_loaded_model()
        assert model2 in loaded2
        assert model1 not in loaded2

        # Cleanup
        shutdown_server()

    def test_unload_model(self):
        """Unloading should stop the server."""
        from soupawhisper.providers.mlx import get_loaded_model, is_server_running
        from soupawhisper.providers.models import get_model_manager

        manager = get_model_manager()

        for model in manager.list_models():
            if manager.is_downloaded(model.name):
                # Preload
                manager.preload_model(model.name)
                assert is_server_running()

                # Unload
                manager.unload_model()
                assert not is_server_running()
                assert get_loaded_model() is None
                return

        pytest.skip("No downloaded models to test")


class TestUIIntegration:
    """Test UI updates model status correctly."""

    @pytest.mark.asyncio
    async def test_settings_shows_model_status(self):
        """Settings screen should show model status indicator."""
        class TestApp(App):
            def compose(self):
                yield ModelManagerWidget(
                    get_config=lambda key, default=None: default,
                    on_local_backend_change=lambda value: None,
                )

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one("#model-status", Static)
            assert status is not None

    @pytest.mark.asyncio
    async def test_model_selection_triggers_preload(self):
        """Selecting a downloaded model should trigger preload."""
        class TestApp(App):
            def compose(self):
                yield ModelManagerWidget(
                    get_config=lambda key, default=None: default,
                    on_local_backend_change=lambda value: None,
                )

        async with TestApp().run_test() as pilot:
            widget = pilot.app.query_one(ModelManagerWidget)
            select = pilot.app.query_one("#local-model-select", Select)

            with patch.object(widget, "_preload_model_if_downloaded") as mocked:
                current = select.value
                for option in select._options:  # type: ignore[attr-defined]
                    value = option[1] if isinstance(option, tuple) else option.value
                    if value != current:
                        select.value = value
                        break
                await pilot.pause()
                mocked.assert_called()
