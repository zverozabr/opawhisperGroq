"""Tests for model download with progress tracking.

TDD tests for:
- Multilingual model filtering
- Progress callback
- Download metrics
- UI progress updates
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from soupawhisper.providers.models import (
    AVAILABLE_MODELS,
    DownloadProgress,
    DownloadResult,
    ModelManager,
    get_model_manager,
)


class TestMultilingualFiltering:
    """Tests for multilingual model filtering."""

    def test_list_multilingual_excludes_english_only(self):
        """list_multilingual() should not return .en models."""
        manager = ModelManager()
        models = manager.list_multilingual()
        names = [m.name for m in models]

        # Should not contain any .en models
        for name in names:
            assert ".en" not in name, f"Found English-only model: {name}"

    def test_list_multilingual_includes_all_base_models(self):
        """list_multilingual() should include all base multilingual models."""
        manager = ModelManager()
        models = manager.list_multilingual()
        names = [m.name for m in models]

        expected = ["tiny", "base", "small", "medium", "large", "large-v3", "turbo"]
        for model in expected:
            assert model in names, f"Missing model: {model}"

    def test_list_multilingual_count(self):
        """Should have exactly 7 multilingual models."""
        manager = ModelManager()
        models = manager.list_multilingual()
        assert len(models) == 7

    def test_available_models_only_multilingual(self):
        """AVAILABLE_MODELS should only contain multilingual models."""
        for name in AVAILABLE_MODELS:
            assert ".en" not in name, f"Found English-only model in AVAILABLE_MODELS: {name}"


class TestDownloadProgress:
    """Tests for DownloadProgress dataclass."""

    def test_percent_calculation(self):
        """Percent should be calculated from bytes."""
        progress = DownloadProgress(
            downloaded_bytes=50_000_000,
            total_bytes=100_000_000,
        )
        assert progress.percent == 50.0

    def test_percent_zero_total(self):
        """Percent should be 0 when total is 0."""
        progress = DownloadProgress(
            downloaded_bytes=0,
            total_bytes=0,
        )
        assert progress.percent == 0.0

    def test_progress_with_speed_and_eta(self):
        """Progress should include speed and ETA."""
        progress = DownloadProgress(
            downloaded_bytes=75_000_000,
            total_bytes=100_000_000,
            speed_mbps=10.0,
            eta_seconds=2.5,
        )
        assert progress.percent == 75.0
        assert progress.speed_mbps == 10.0
        assert progress.eta_seconds == 2.5


class TestDownloadResult:
    """Tests for DownloadResult dataclass."""

    def test_avg_speed_calculation(self):
        """Average speed should be calculated from size and time."""
        result = DownloadResult(
            model_name="base",
            path=Path("/tmp/base"),
            size_bytes=100_000_000,  # 100 MB
            download_time_seconds=10.0,
        )
        # 100 MB / 10s = 10 MB/s
        assert abs(result.avg_speed_mbps - 9.5367) < 0.1  # ~95.37 MB / 10s

    def test_avg_speed_zero_time(self):
        """Average speed should be 0 when time is 0."""
        result = DownloadResult(
            model_name="tiny",
            path=Path("/tmp/tiny"),
            size_bytes=74_000_000,
            download_time_seconds=0,
        )
        assert result.avg_speed_mbps == 0.0


class TestModelManagerDownload:
    """Tests for ModelManager download methods."""

    def test_download_for_mlx_returns_download_result(self):
        """download_for_mlx should return DownloadResult."""
        with patch("huggingface_hub.snapshot_download"):
            manager = ModelManager(models_dir=Path("/tmp/test_models"))
            
            # Mock get_size_on_disk to return a value
            with patch.object(manager, "get_size_on_disk", return_value=74_000_000):
                result = manager.download_for_mlx("tiny")
                
                assert isinstance(result, DownloadResult)
                assert result.model_name == "tiny"
                assert result.size_bytes == 74_000_000

    def test_download_calls_progress_callback(self):
        """download_for_mlx should call progress callback."""
        callback = MagicMock()
        
        with patch("huggingface_hub.snapshot_download"):
            manager = ModelManager(models_dir=Path("/tmp/test_models"))
            
            with patch.object(manager, "get_size_on_disk", return_value=74_000_000):
                manager.download_for_mlx("tiny", progress_callback=callback)
                
                # Final callback should be called
                assert callback.called
                # Check last call was with 100% progress
                last_call = callback.call_args[0][0]
                assert isinstance(last_call, DownloadProgress)
                assert last_call.percent == 100.0

    def test_download_for_faster_whisper_returns_result(self):
        """download_for_faster_whisper should return DownloadResult."""
        with patch("faster_whisper.WhisperModel"):
            manager = ModelManager(models_dir=Path("/tmp/test_models"))
            result = manager.download_for_faster_whisper("base")
            
            assert isinstance(result, DownloadResult)
            assert result.model_name == "base"

    def test_download_unknown_model_raises(self):
        """Downloading unknown model should raise ValueError."""
        manager = ModelManager()
        
        with pytest.raises(ValueError, match="Unknown MLX model"):
            manager.download_for_mlx("nonexistent")


class TestModelInfo:
    """Tests for ModelInfo structure."""

    def test_all_models_have_mlx_repo(self):
        """All multilingual models should have MLX repo."""
        for name, info in AVAILABLE_MODELS.items():
            if ".en" not in name:
                assert info.mlx_repo is not None, f"Model {name} missing mlx_repo"

    def test_all_models_have_faster_whisper_name(self):
        """All models should have faster_whisper_name."""
        for name, info in AVAILABLE_MODELS.items():
            assert info.faster_whisper_name is not None, f"Model {name} missing faster_whisper_name"

    def test_model_sizes_reasonable(self):
        """Model sizes should be reasonable."""
        for name, info in AVAILABLE_MODELS.items():
            assert info.size_mb > 0, f"Model {name} has invalid size"
            assert info.size_mb < 5000, f"Model {name} has unreasonably large size"


class TestSingletonManager:
    """Tests for singleton ModelManager."""

    def test_get_model_manager_returns_same_instance(self):
        """get_model_manager() should return same instance."""
        # Reset singleton for test
        import soupawhisper.providers.models as m
        m._manager = None
        
        manager1 = get_model_manager()
        manager2 = get_model_manager()
        
        assert manager1 is manager2
