"""Main application logic."""

import threading
from pathlib import Path
from typing import Callable, Optional

from .audio import AudioRecorder
from .backend import DisplayBackend, create_backend
from .config import Config
from .logging import get_logger
from .output import notify
from .storage import DebugStorage
from .transcription_handler import TranscriptionContext, TranscriptionHandler

log = get_logger()


def validate_config(config: Config) -> list[str]:
    """Validate configuration before running the app."""
    errors: list[str] = []
    if not config.active_provider.startswith("local-") and not config.api_key:
        errors.append("Groq API key not configured!")
    return errors


class App:
    """Voice dictation application.

    Responsibilities:
    - Manage hotkey listening
    - Control audio recording
    - Delegate transcription to TranscriptionHandler
    """

    def __init__(
        self,
        config: Config,
        backend: DisplayBackend | None = None,
        on_transcription: Optional[Callable[[str, str], None]] = None,
        on_recording: Optional[Callable[[bool], None]] = None,
        on_transcribing: Optional[Callable[[bool], None]] = None,
    ):
        """Initialize application.

        Args:
            config: Application configuration
            backend: Display backend (auto-created if None)
            on_transcription: Optional callback(text, language) when transcription completes
            on_recording: Optional callback(is_recording) when recording state changes
            on_transcribing: Optional callback(is_transcribing) when transcription state changes
        """
        self.config = config
        self.recorder = AudioRecorder(device=config.audio_device)
        self.backend = backend or create_backend(config.backend, config.typing_delay)
        self.on_transcription = on_transcription
        self.on_recording = on_recording
        self.on_transcribing = on_transcribing
        self._debug_storage = DebugStorage() if config.debug else None
        self._transcription_handler = TranscriptionHandler(config)
        self._transcribing = False

        if not config.api_key and not config.active_provider.startswith("local-"):
            log.warning("Groq API key not configured!")

    def _notify(self, title: str, message: str, icon: str = "dialog-information", timeout: int = 2000) -> None:
        if self.config.notifications:
            notify(title, message, icon, timeout)

    def _on_press(self) -> None:
        import time
        press_time = time.perf_counter()

        if self.recorder.is_recording:
            return

        self.recorder.start()
        start_time = time.perf_counter()
        latency_ms = (start_time - press_time) * 1000
        log.debug(f"Hotkey→Recording latency: {latency_ms:.1f}ms")

        log.info("Recording...")
        # No notification - menu bar indicator shows recording status
        if self.on_recording:
            self.on_recording(True)

    def _on_release(self) -> None:
        import time
        release_time = time.perf_counter()

        if not self.recorder.is_recording:
            return

        audio_path = self.recorder.stop()
        stop_time = time.perf_counter()
        stop_latency_ms = (stop_time - release_time) * 1000
        log.debug(f"Release→Stop latency: {stop_latency_ms:.1f}ms")

        if self.on_recording:
            self.on_recording(False)
        if not audio_path:
            return

        # Run transcription in background thread to not block hotkey listener
        thread = threading.Thread(
            target=self._transcribe_async,
            args=(audio_path, release_time),
            daemon=True,
        )
        thread.start()

    def _transcribe_async(self, audio_path: str, release_time: float = 0) -> None:
        """Transcribe audio in background thread."""
        import time

        if self._transcribing:
            log.warning("Already transcribing, skipping")
            return

        self._transcribing = True
        if self.on_transcribing:
            self.on_transcribing(True)

        transcribe_start = time.perf_counter()

        try:
            ctx = TranscriptionContext(
                audio_path=Path(audio_path),
                config=self.config,
                backend=self.backend,
                debug_storage=self._debug_storage,
                on_complete=self.on_transcription,
            )
            self._transcription_handler.handle(ctx)

            transcribe_end = time.perf_counter()
            transcribe_ms = (transcribe_end - transcribe_start) * 1000
            total_ms = (transcribe_end - release_time) * 1000 if release_time else 0
            log.debug(f"Transcription time: {transcribe_ms:.0f}ms")
            if release_time:
                log.debug(f"Total release→result: {total_ms:.0f}ms")
        finally:
            self.recorder.cleanup()
            self._transcribing = False
            if self.on_transcribing:
                self.on_transcribing(False)

    def stop(self) -> None:
        """Stop the application."""
        self.backend.stop()

    def run(self) -> None:
        """Start the application."""
        log.info(f"Ready! Hold [{self.config.hotkey}] to record.")
        log.info("Press Ctrl+C to quit.")

        self.backend.listen_hotkey(
            self.config.hotkey,
            self._on_press,
            self._on_release,
        )
