"""Widget for managing local models."""

from typing import Callable

from textual.containers import Horizontal
from textual.widgets import Button, Label, ProgressBar, Select, Static


def get_model_manager():
    """Get ModelManager instance (lazy import)."""
    from soupawhisper.providers.models import get_model_manager as _get

    return _get()


class ModelManagerWidget(Static):
    """Local model management UI (download, delete, preload)."""

    def __init__(
        self,
        get_config: Callable[[str, str], str],
        on_local_backend_change: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._get_config = get_config
        self._on_local_backend_change = on_local_backend_change

    def compose(self):
        """Compose Local tab content."""
        with Horizontal(classes="field-row"):
            yield Label("Backend", classes="field-label")
            yield Select(
                options=[
                    ("MLX (Apple Silicon)", "mlx"),
                    ("CPU (Cross-platform)", "cpu"),
                ],
                value=self._get_config("local_backend", "mlx"),
                id="local-backend-select",
                classes="field-input",
            )

        with Horizontal(classes="field-row"):
            yield Label("Model", classes="field-label")
            yield Select(
                options=self._get_local_model_options(),
                value=self._get_default_local_model(),
                id="local-model-select",
                classes="field-input",
            )

        with Horizontal(classes="field-row model-info-row"):
            yield Label("Status", classes="field-label")
            yield Static("○ Not downloaded", id="model-status", classes="field-input model-status")

        with Horizontal(classes="field-row model-info-row"):
            yield Label("Size", classes="field-label")
            yield Static("~142 MB", id="model-size", classes="field-input")

        with Horizontal(classes="button-row"):
            yield Button("⬇️  Download", id="download-model", variant="primary")
            yield Button("🗑️  Delete", id="delete-model", variant="error")

        yield ProgressBar(id="download-progress", show_eta=True, total=100)

    def on_mount(self) -> None:
        """Update status on mount."""
        self._update_model_status()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle Select changes inside widget."""
        if event.select.id == "local-backend-select":
            self._on_local_backend_change(str(event.value))
            event.stop()
            return

        if event.select.id == "local-model-select":
            model_name = str(event.value) if event.value else "base"
            self._update_model_info(model_name)
            self._update_local_provider_model(model_name)
            self._preload_model_if_downloaded(model_name)
            event.stop()
            return

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses inside widget."""
        if event.button.id == "download-model":
            self._download_model()
            event.stop()
        elif event.button.id == "delete-model":
            self._delete_model()
            event.stop()

    def _get_default_local_model(self) -> str:
        """Get default local model from providers.json or fallback."""
        try:
            from soupawhisper.providers import load_providers_config
            from soupawhisper.providers.model_names import ModelNameResolver

            config = load_providers_config()
            providers = config.get("providers", {})

            backend = self._get_config("local_backend", "mlx")
            provider_name = f"local-{backend}"

            if provider_name in providers:
                model = providers[provider_name].get("model", "base")
                if not model or model == "Select.BLANK":
                    return "base"
                return ModelNameResolver.extract_short_name(model)

            return "base"
        except Exception:
            return "base"

    def _get_local_model_options(self):
        """Get available local model options from ModelManager (multilingual only)."""
        try:
            manager = get_model_manager()
            options = []
            for model in manager.list_multilingual():
                is_downloaded = manager.is_downloaded(model.name)
                icon = "✓" if is_downloaded else "○"
                label = f"{icon} {model.name} ({model.size_mb} MB)"
                options.append((label, model.name))
            return options
        except Exception:
            return [
                ("○ tiny (74 MB)", "tiny"),
                ("○ base (142 MB)", "base"),
                ("○ small (466 MB)", "small"),
                ("○ medium (1.5 GB)", "medium"),
                ("○ large (2.9 GB)", "large"),
                ("○ large-v3 (3.1 GB)", "large-v3"),
                ("○ turbo (1.6 GB)", "turbo"),
            ]

    def _update_local_provider_model(self, model_name: str) -> None:
        """Update model in providers.json for active local provider."""
        try:
            from soupawhisper.providers import load_providers_config, save_providers_config

            config = load_providers_config()
            providers = config.get("providers", {})

            backend = self._get_config("local_backend", "mlx")
            provider_name = f"local-{backend}"

            if provider_name in providers and model_name != "Select.BLANK":
                providers[provider_name]["model"] = model_name
                save_providers_config(config)
        except Exception:
            pass

    def _update_model_info(self, model_name: str) -> None:
        """Update model size and status display."""
        try:
            from soupawhisper.providers.models import ModelStatus

            status = self.query_one("#model-status", Static)
            size_label = self.query_one("#model-size", Static)
            manager = get_model_manager()
            model_info = manager.get_model_info(model_name)

            if model_info:
                size_label.update(f"~{model_info.size_mb} MB")

            model_status = manager.get_model_status(model_name)

            if model_status == ModelStatus.LOADED:
                disk_size = manager.get_size_on_disk(model_name)
                disk_mb = disk_size // (1024 * 1024)
                status.update(f"🟢 Loaded in memory ({disk_mb} MB)")
                status.add_class("-loaded")
                status.remove_class("-downloaded", "-not-downloaded", "-loading")
            elif model_status == ModelStatus.LOADING:
                status.update("⏳ Loading into memory...")
                status.add_class("-loading")
                status.remove_class("-downloaded", "-not-downloaded", "-loaded")
            elif model_status == ModelStatus.DOWNLOADED:
                disk_size = manager.get_size_on_disk(model_name)
                disk_mb = disk_size // (1024 * 1024)
                status.update(f"✓ Downloaded ({disk_mb} MB)")
                status.add_class("-downloaded")
                status.remove_class("-not-downloaded", "-loaded", "-loading")
            else:
                status.update("○ Not downloaded")
                status.add_class("-not-downloaded")
                status.remove_class("-downloaded", "-loaded", "-loading")
        except Exception:
            pass

    def _preload_model_if_downloaded(self, model_name: str) -> None:
        """Preload model into memory if it's downloaded."""
        manager = get_model_manager()

        if not manager.is_downloaded(model_name):
            return

        try:
            status = self.query_one("#model-status", Static)
            status.update("⏳ Loading into memory...")
            status.add_class("-loading")
        except Exception:
            pass

        def do_preload():
            try:
                manager.preload_model(model_name)
                self.call_from_thread(self._update_model_info, model_name)
                return True
            except Exception:
                self.call_from_thread(self._update_model_info, model_name)
                return False

        self.run_worker(do_preload, thread=True, exit_on_error=False)

    def _download_model(self) -> None:
        """Download the selected local model using run_worker for async."""
        import sys

        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)
        progress = self.query_one("#download-progress", ProgressBar)

        model_name = str(model_select.value) if model_select.value else "base"

        manager = get_model_manager()
        model_info = manager.get_model_info(model_name)
        size_mb = model_info.size_mb if model_info else 100

        status.update(f"⬇️  Downloading {model_name} ({size_mb} MB)...")
        progress.remove_class("-hidden")
        progress.update(progress=0, total=100)

        def on_progress(prog):
            self.call_from_thread(self._update_download_progress, prog)

        def do_download():
            try:
                mgr = get_model_manager()
                if sys.platform == "darwin":
                    try:
                        return mgr.download_for_mlx(model_name, on_progress)
                    except Exception:
                        return mgr.download_for_faster_whisper(model_name, on_progress)
                else:
                    return mgr.download_for_faster_whisper(model_name, on_progress)
            except Exception as e:
                return e

        self.run_worker(do_download, thread=True, name=f"download-{model_name}")

    def _update_download_progress(self, prog) -> None:
        """Update UI with download progress."""
        try:
            status = self.query_one("#model-status", Static)
            progress = self.query_one("#download-progress", ProgressBar)

            progress.update(progress=prog.percent)

            if prog.speed_mbps > 0:
                eta_str = (
                    f"{prog.eta_seconds:.0f}s"
                    if prog.eta_seconds < 60
                    else f"{prog.eta_seconds/60:.1f}m"
                )
                status.update(
                    f"⬇️  {prog.percent:.0f}% | {prog.speed_mbps:.1f} MB/s | ETA: {eta_str}"
                )
        except Exception:
            pass

    def on_worker_state_changed(self, event) -> None:
        """Handle worker completion."""
        if event.worker.name and event.worker.name.startswith("download-"):
            if event.worker.is_finished:
                result = event.worker.result
                if isinstance(result, Exception):
                    self._handle_download_error(result)
                else:
                    self._finish_download(result)

    def _handle_download_error(self, error: Exception) -> None:
        """Handle download error."""
        try:
            status = self.query_one("#model-status", Static)
            progress = self.query_one("#download-progress", ProgressBar)
            status.update(f"❌ Error: {error}")
            progress.add_class("-hidden")
        except Exception:
            pass

    def _finish_download(self, result) -> None:
        """Finish download and show metrics."""
        try:
            status = self.query_one("#model-status", Static)
            progress = self.query_one("#download-progress", ProgressBar)

            if hasattr(result, "model_name"):
                size_mb = result.size_bytes / 1024 / 1024
                status.update(
                    f"✓ {result.model_name} | {size_mb:.0f} MB | "
                    f"{result.download_time_seconds:.1f}s | {result.avg_speed_mbps:.1f} MB/s"
                )
            else:
                status.update("✓ Downloaded")

            progress.update(progress=100)
            progress.add_class("-hidden")
            self._refresh_model_list()
        except Exception:
            pass

    def _delete_model(self) -> None:
        """Delete the selected local model using ModelManager."""
        model_select = self.query_one("#local-model-select", Select)
        status = self.query_one("#model-status", Static)

        model_name = str(model_select.value) if model_select.value else "base"
        status.update(f"🗑️  Deleting {model_name}...")

        try:
            manager = get_model_manager()
            if manager.delete(model_name):
                self._finish_delete(model_name)
            else:
                status.update("○ Model not found locally")
        except Exception as e:
            status.update(f"❌ Error: {e}")

    def _finish_delete(self, model_name: str) -> None:
        """Finish delete and update UI."""
        self._update_model_info(model_name)
        self._refresh_model_list()

    def _refresh_model_list(self) -> None:
        """Refresh model list to show updated download status."""
        try:
            model_select = self.query_one("#local-model-select", Select)
            current_value = model_select.value
            model_select.set_options(self._get_local_model_options())
            if current_value:
                model_select.value = current_value
        except Exception:
            pass

    def _update_model_status(self) -> None:
        """Update model status display for current selection."""
        try:
            model_select = self.query_one("#local-model-select", Select)
            model_name = str(model_select.value) if model_select.value else "base"
            self._update_model_info(model_name)
        except Exception:
            pass

    def update_model_status(self) -> None:
        """Public wrapper to refresh model status."""
        self._update_model_status()
