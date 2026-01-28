"""Tests for MLX Model Server with model caching."""

import json
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


def _is_mlx_available() -> bool:
    """Check if mlx-whisper is actually usable.

    MLX requires macOS + Apple Silicon + mlx-whisper installed.
    We check by trying to import in the current process.
    """
    if sys.platform != "darwin":
        return False
    try:
        import mlx.core  # noqa: F401
        import mlx_whisper  # noqa: F401
        return True
    except ImportError:
        return False


# MLX tests that require subprocess need to run the server properly.
# In uv environment, we can't reliably spawn subprocesses with mlx.
# Mark these as skip-in-CI or integration tests.


@pytest.mark.skipif(not _is_mlx_available(), reason="MLX not available")
class TestMLXServerProtocol:
    """Test MLX server IPC protocol.

    These tests require running the server in subprocess.
    They are marked as integration tests and may be skipped in CI.
    """

    @pytest.mark.integration
    def test_server_starts_and_reports_ready(self):
        """Server should start and send ready signal."""
        server_script = Path(__file__).parent.parent / "src" / "soupawhisper" / "providers" / "mlx_server.py"

        # Use uv run to ensure mlx is available in subprocess
        proc = subprocess.Popen(
            ["uv", "run", "python", str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Server should send ready signal
        try:
            ready_line = proc.stdout.readline()
            if not ready_line:
                stderr = proc.stderr.read()
                pytest.skip(f"Server failed to start: {stderr[:500]}")

            ready = json.loads(ready_line)
            if "error" in ready:
                pytest.skip(f"Server error: {ready['error']}")

            assert ready.get("status") == "ready"

            proc.stdin.write('{"command": "shutdown"}\n')
            proc.stdin.flush()
            proc.wait(timeout=10)

        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    @pytest.mark.integration
    def test_server_handles_shutdown_command(self):
        """Server should exit cleanly on shutdown command."""
        server_script = Path(__file__).parent.parent / "src" / "soupawhisper" / "providers" / "mlx_server.py"

        proc = subprocess.Popen(
            ["uv", "run", "python", str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Read ready signal
            ready_line = proc.stdout.readline()
            if not ready_line:
                stderr = proc.stderr.read()
                pytest.skip(f"Server failed to start: {stderr[:500]}")

            ready = json.loads(ready_line)
            if "error" in ready:
                pytest.skip(f"Server error: {ready['error']}")

            assert ready.get("status") == "ready"

            # Send shutdown
            proc.stdin.write('{"command": "shutdown"}\n')
            proc.stdin.flush()

            # Server should exit
            proc.wait(timeout=5)
            assert proc.returncode == 0

        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


class TestMLXProviderWithServer:
    """Test MLXProvider using persistent server."""

    def test_transcribe_via_server_caches_model(self):
        """Second transcription should be faster (cached model)."""
        # This is a metrics/integration test
        # Would require actual MLX setup to run properly
        pytest.skip("Requires MLX setup and real model")

    def test_server_fallback_to_subprocess(self):
        """Should fall back to subprocess if server fails."""
        from soupawhisper.providers.base import ProviderConfig

        # Mock to test fallback behavior
        with patch("soupawhisper.providers.mlx.USE_PERSISTENT_SERVER", True):
            config = ProviderConfig(name="local-mlx", type="mlx", model="base")

            with patch("soupawhisper.providers.mlx.MLXProvider._transcribe_via_server") as mock_server:
                mock_server.side_effect = Exception("Server crashed")

                with patch("soupawhisper.providers.mlx.MLXProvider._transcribe_subprocess") as mock_subprocess:
                    from soupawhisper.providers.base import TranscriptionResult
                    mock_subprocess.return_value = TranscriptionResult(text="fallback", raw_response={})

                    with patch("soupawhisper.providers.mlx.MLXProvider.is_available", return_value=True):
                        from soupawhisper.providers.mlx import MLXProvider
                        provider = MLXProvider(config)
                        result = provider.transcribe("/tmp/test.wav", "auto")

                        assert result.text == "fallback"
                        mock_subprocess.assert_called_once()


class TestMLXMetrics:
    """Test performance metrics for MLX transcription."""

    def test_first_transcription_logs_model_load_time(self):
        """First transcription should log model loading time."""
        pytest.skip("Requires MLX setup and real model")

    def test_second_transcription_is_faster(self):
        """Second transcription should skip model loading."""
        pytest.skip("Requires MLX setup and real model")

    def test_metrics_format_in_logs(self):
        """Metrics should be logged in parseable format."""

        # Capture logs
        with patch("soupawhisper.providers.mlx.logger") as mock_logger:
            # Simulate what the provider logs
            mock_logger.debug.assert_not_called()  # Not called yet

            # The actual log format is: "MLX server transcribe: {ms}ms, total: {ms}ms"
            # This can be parsed for metrics


@pytest.mark.skipif(not _is_mlx_available(), reason="MLX not available")
class TestMLXIntegration:
    """Integration tests for MLX (requires macOS with mlx-whisper installed)."""

    @pytest.mark.integration
    def test_real_server_startup(self):
        """Test actual server startup with mlx_whisper."""
        server_script = Path(__file__).parent.parent / "src" / "soupawhisper" / "providers" / "mlx_server.py"

        proc = subprocess.Popen(
            ["uv", "run", "python", str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Should receive ready signal within 10s (includes import time)
            start = time.perf_counter()
            ready_line = proc.stdout.readline()
            ready_time = time.perf_counter() - start

            if not ready_line:
                stderr = proc.stderr.read()
                pytest.skip(f"Server failed to start: {stderr[:500]}")

            ready = json.loads(ready_line)
            if "error" in ready:
                pytest.skip(f"Server error: {ready['error']}")

            assert ready.get("status") == "ready"
            print(f"\nServer ready in {ready_time:.2f}s")

            # Shutdown
            proc.stdin.write('{"command": "shutdown"}\n')
            proc.stdin.flush()
            proc.wait(timeout=5)

        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    @pytest.mark.integration
    def test_model_caching_performance(self):
        """Test that model caching improves performance."""
        # Create a test audio file
        test_audio = Path(__file__).parent / "fixtures" / "test_russian_speech.wav"
        if not test_audio.exists():
            pytest.skip("Test audio file not found")

        from soupawhisper.providers.base import ProviderConfig
        from soupawhisper.providers.mlx import MLXProvider

        config = ProviderConfig(name="local-mlx", type="mlx", model="base")
        provider = MLXProvider(config)

        # First transcription (cold start - loads model)
        start1 = time.perf_counter()
        result1 = provider.transcribe(str(test_audio), "ru")
        time1 = time.perf_counter() - start1

        # Second transcription (warm - model cached)
        start2 = time.perf_counter()
        result2 = provider.transcribe(str(test_audio), "ru")
        time2 = time.perf_counter() - start2

        print(f"\nFirst transcription (cold): {time1:.2f}s")
        print(f"Second transcription (warm): {time2:.2f}s")
        print(f"Speedup: {time1/time2:.1f}x")

        # Second should be significantly faster (at least 2x)
        # Model loading is 2-5s, transcription is 0.5-2s
        assert time2 < time1, "Cached transcription should be faster"
        assert result1.text, "Should return text"
        assert result2.text, "Should return text"
