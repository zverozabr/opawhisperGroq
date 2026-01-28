"""Background worker management.

Single Responsibility: Manage background threads for hotkey listening.
Framework-agnostic: Works with both GUI (Flet) and TUI (Textual).

SOLID/DIP: Depends on CoreApp Protocol, not concrete App implementation.
"""

import threading
from typing import TYPE_CHECKING, Callable, Optional, Protocol

from soupawhisper.config import Config
from soupawhisper.logging import get_logger

if TYPE_CHECKING:
    pass

log = get_logger()


class CoreApp(Protocol):
    """Protocol for core application.

    SOLID/DIP: WorkerManager depends on this abstraction, not concrete App.
    This allows for testing and alternative implementations.
    """

    def run(self) -> None:
        """Run the core application loop."""
        ...

    def stop(self) -> None:
        """Stop the core application."""
        ...


class WorkerManager:
    """Manages background worker threads.

    Handles:
    - Starting the core app in a background thread
    - Graceful shutdown

    Framework-agnostic: Does not depend on Flet or Textual.
    The run_in_thread callable is provided by the UI framework.
    """

    def __init__(
        self,
        config: Config,
        on_transcription: Optional[Callable[[str, str], None]] = None,
        on_recording: Optional[Callable[[bool], None]] = None,
        on_transcribing: Optional[Callable[[bool], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """Initialize worker manager.

        Args:
            config: Application configuration.
            on_transcription: Callback when transcription completes (text, language).
            on_recording: Callback when recording state changes.
            on_transcribing: Callback when transcription state changes.
            on_error: Callback when an error occurs.
        """
        self.config = config
        self._on_transcription = on_transcription
        self._on_recording = on_recording
        self._on_transcribing = on_transcribing
        self._on_error = on_error
        self._core: Optional[CoreApp] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    @property
    def core(self) -> Optional[CoreApp]:
        """Get the core app instance."""
        return self._core

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    def start(self) -> None:
        """Start the worker in a new thread."""
        if self._running:
            log.warning("Worker already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def start_with_runner(self, run_in_thread: Callable[[Callable[[], None]], None]) -> None:
        """Start the worker using provided thread runner.

        This is for frameworks that provide their own thread management
        (e.g., Flet's page.run_thread, Textual's run_worker).

        Args:
            run_in_thread: Function to run the worker loop in a thread.
        """
        if self._running:
            log.warning("Worker already running")
            return

        self._running = True
        run_in_thread(self._worker_loop)

    def stop(self) -> None:
        """Stop the worker and cleanup."""
        self._running = False
        if self._core:
            self._core.stop()
            self._core = None

    def _worker_loop(self) -> None:
        """Background worker that runs the core app.

        SOLID/DIP: Creates App through factory, could be injected for testing.
        """
        try:
            # Import here to avoid circular imports and allow DIP
            from soupawhisper.app import App
            from soupawhisper.backend import create_backend

            backend = create_backend(self.config.backend, self.config.typing_delay)
            self._core = App(
                config=self.config,
                backend=backend,
                on_transcription=self._on_transcription,
                on_recording=self._on_recording,
                on_transcribing=self._on_transcribing,
            )
            self._core.run()
        except Exception as e:
            log.error(f"Worker error: {e}")
            if self._on_error:
                self._on_error(str(e))
        finally:
            self._running = False
