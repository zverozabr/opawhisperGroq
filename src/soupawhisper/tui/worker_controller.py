"""Worker controller for TUI application.

Single Responsibility: Manage worker lifecycle and thread-safe callbacks.
Extracted from TUIApp for SRP compliance.
"""

from typing import Callable, Optional

from soupawhisper.config import Config
from soupawhisper.logging import get_logger
from soupawhisper.worker import WorkerManager

log = get_logger()


class WorkerController:
    """Controls worker lifecycle and provides thread-safe callbacks.

    SRP: This class only handles worker management, not UI logic.
    """

    def __init__(
        self,
        config: Config,
        call_from_thread: Callable,
        on_recording: Optional[Callable[[bool], None]] = None,
        on_transcribing: Optional[Callable[[bool], None]] = None,
        on_transcription: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """Initialize worker controller.

        Args:
            config: Application config.
            call_from_thread: Thread-safe callback dispatcher (from Textual App).
            on_recording: Callback for recording state changes.
            on_transcribing: Callback for transcribing state changes.
            on_transcription: Callback for transcription completion.
            on_error: Callback for errors.
        """
        self._config = config
        self._call_from_thread = call_from_thread
        self._on_recording = on_recording
        self._on_transcribing = on_transcribing
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._worker: Optional[WorkerManager] = None

    def start(self) -> None:
        """Start the background worker."""
        self._worker = WorkerManager(
            config=self._config,
            on_transcription=self._wrap(self._on_transcription),
            on_recording=self._wrap(self._on_recording),
            on_transcribing=self._wrap(self._on_transcribing),
            on_error=self._wrap(self._on_error),
        )
        self._worker.start()
        log.info("Worker started")

    def stop(self) -> None:
        """Stop the background worker."""
        if self._worker:
            self._worker.stop()
            log.info("Worker stopped")

    def restart(self) -> None:
        """Restart the background worker."""
        self.stop()
        self.start()

    def pause(self) -> None:
        """Pause the background worker (stop hotkey listening)."""
        if self._worker:
            self._worker.stop()
            log.debug("Worker paused")

    def resume(self) -> None:
        """Resume the background worker (restart hotkey listening)."""
        self.start()

    def _wrap(self, callback: Optional[Callable]) -> Optional[Callable]:
        """Wrap callback to be thread-safe.

        Args:
            callback: Original callback.

        Returns:
            Thread-safe wrapper or None if callback is None.
        """
        if callback is None:
            return None
        return lambda *args: self._call_from_thread(callback, *args)
