"""TDD: Test MLX transcription in background thread.

This test reproduces the "bad value(s) in fds_to_keep" error
that occurs when running MLX transcription in a background thread.
"""

import threading
import pytest


class TestMLXInBackgroundThread:
    """Test MLX transcription works in background thread."""

    @pytest.mark.skipif(
        __import__("sys").platform != "darwin",
        reason="MLX only available on macOS"
    )
    def test_mlx_transcription_in_thread(self):
        """MLX transcription should work in background thread."""
        from soupawhisper.providers.mlx import MLXProvider
        from soupawhisper.providers.base import ProviderConfig
        
        config = ProviderConfig(
            name="test-mlx",
            type="mlx",
            model="medium",
        )
        provider = MLXProvider(config)
        
        if not provider.is_available():
            pytest.skip("MLX not available")
        
        result = None
        error = None
        
        def run_in_thread():
            nonlocal result, error
            try:
                result = provider.transcribe(
                    "tests/fixtures/test_russian_speech.wav",
                    "ru"
                )
            except Exception as e:
                error = e
        
        # Run in background thread (like TUI worker does)
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=60)
        
        # Should not have error
        assert error is None, f"MLX failed in thread: {error}"
        assert result is not None
        assert len(result.text) > 0

    @pytest.mark.skipif(
        __import__("sys").platform != "darwin",
        reason="MLX only available on macOS"
    )
    def test_mlx_with_worker_manager(self):
        """MLX should work through WorkerManager like TUI uses."""
        import time
        from soupawhisper.config import Config
        from soupawhisper.worker import WorkerManager
        
        config = Config.load()
        config.active_provider = "local-mlx"
        
        transcription_result = None
        error_result = None
        
        def on_transcription(text, lang):
            nonlocal transcription_result
            transcription_result = text
            
        def on_error(err):
            nonlocal error_result
            error_result = err
        
        worker = WorkerManager(
            config=config,
            on_transcription=on_transcription,
            on_error=on_error,
        )
        
        # Start worker (runs App in background thread)
        worker.start()
        
        # Wait for worker to initialize
        time.sleep(2)
        
        # Simulate hotkey press and release
        if worker.core:
            worker.core._on_press()
            time.sleep(3)  # Record for 3 seconds
            worker.core._on_release()
            
            # Wait for transcription
            time.sleep(30)
        
        worker.stop()
        
        # Should have transcription or no error
        assert error_result is None, f"Worker error: {error_result}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        __import__("sys").platform != "darwin",
        reason="MLX only available on macOS"
    )
    async def test_mlx_in_textual_app(self):
        """MLX should work inside Textual app context."""
        import asyncio
        from textual.app import App, ComposeResult
        from textual.widgets import Static
        
        from soupawhisper.providers.mlx import MLXProvider
        from soupawhisper.providers.base import ProviderConfig
        
        config = ProviderConfig(
            name="test-mlx",
            type="mlx",
            model="medium",
        )
        provider = MLXProvider(config)
        
        if not provider.is_available():
            pytest.skip("MLX not available")
        
        result_holder = {"result": None, "error": None}
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Static("Testing MLX")
            
            def on_mount(self) -> None:
                # Run MLX in worker thread (like TUI does)
                self.run_worker(self._test_mlx, thread=True)
            
            async def _test_mlx(self) -> None:
                try:
                    result = provider.transcribe(
                        "tests/fixtures/test_russian_speech.wav",
                        "ru"
                    )
                    result_holder["result"] = result.text
                except Exception as e:
                    result_holder["error"] = str(e)
                finally:
                    self.exit()
        
        app = TestApp()
        async with app.run_test() as pilot:
            # Wait for worker to complete
            await asyncio.sleep(30)
        
        assert result_holder["error"] is None, f"MLX error in Textual: {result_holder['error']}"
        assert result_holder["result"] is not None

    @pytest.mark.skipif(
        __import__("sys").platform != "darwin",
        reason="MLX only available on macOS"
    )
    def test_mlx_before_textual(self):
        """MLX should work if run BEFORE Textual app starts."""
        from soupawhisper.providers.mlx import MLXProvider
        from soupawhisper.providers.base import ProviderConfig
        
        config = ProviderConfig(
            name="test-mlx",
            type="mlx",
            model="medium",
        )
        provider = MLXProvider(config)
        
        if not provider.is_available():
            pytest.skip("MLX not available")
        
        # First, run MLX (before Textual)
        result1 = provider.transcribe("tests/fixtures/test_russian_speech.wav", "ru")
        assert result1.text is not None
        print(f"Pre-Textual result: {result1.text}")
        
        # Now run Textual app
        import asyncio
        from textual.app import App, ComposeResult
        from textual.widgets import Static
        
        class DummyApp(App):
            def compose(self) -> ComposeResult:
                yield Static("Dummy")
            
            def on_mount(self):
                self.exit()
        
        asyncio.get_event_loop().run_until_complete(
            DummyApp().run_async()
        )
        
        # Try MLX again (after Textual)
        result2 = provider.transcribe("tests/fixtures/test_russian_speech.wav", "ru")
        assert result2.text is not None
        print(f"Post-Textual result: {result2.text}")
