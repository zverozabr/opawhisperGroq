"""Main application logic."""

import sys
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

        if not config.api_key:
            log.error("Groq API key not configured!")
            log.error("Add your API key to ~/.config/soupawhisper/config.ini")
            sys.exit(1)

    def _notify(self, title: str, message: str, icon: str = "dialog-information", timeout: int = 2000) -> None:
        if self.config.notifications:
            notify(title, message, icon, timeout)

    def _on_press(self) -> None:
        if self.recorder.is_recording:
            return

        self.recorder.start()
        log.info("Recording...")
        self._notify("Recording...", "Release key when done", "audio-input-microphone", 30000)
        if self.on_recording:
            self.on_recording(True)

    def _on_release(self) -> None:
        if not self.recorder.is_recording:
            return

        audio_path = self.recorder.stop()
        if self.on_recording:
            self.on_recording(False)
        if not audio_path:
            return

        # Run transcription in background thread to not block hotkey listener
        thread = threading.Thread(
            target=self._transcribe_async,
            args=(audio_path,),
            daemon=True,
        )
        thread.start()

    def _transcribe_async(self, audio_path: str) -> None:
        """Transcribe audio in background thread."""
        if self._transcribing:
            log.warning("Already transcribing, skipping")
            return

        self._transcribing = True
        if self.on_transcribing:
            self.on_transcribing(True)
        try:
            ctx = TranscriptionContext(
                audio_path=Path(audio_path),
                config=self.config,
                backend=self.backend,
                debug_storage=self._debug_storage,
                on_complete=self.on_transcription,
            )
            self._transcription_handler.handle(ctx)
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
