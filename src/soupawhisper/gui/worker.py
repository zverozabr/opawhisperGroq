"""Background worker management for GUI.

Single Responsibility: Manage background threads for hotkey listening.
"""

import os
import subprocess
import sys
import threading
import time
from typing import Callable, Optional

from soupawhisper.app import App
from soupawhisper.backend import create_backend
from soupawhisper.config import Config
from soupawhisper.logging import get_logger

log = get_logger()


class WorkerManager:
    """Manages background worker threads for the GUI.
    
    Handles:
    - Starting the core app in a background thread
    - Monitoring the Flet process for cleanup
    - Graceful shutdown
    """

    def __init__(
        self,
        config: Config,
        on_transcription: Optional[Callable[[str, str], None]] = None,
        on_recording: Optional[Callable[[bool], None]] = None,
        on_transcribing: Optional[Callable[[bool], None]] = None,
        on_worker_done: Optional[Callable[[], None]] = None,
    ):
        """Initialize worker manager.
        
        Args:
            config: Application configuration
            on_transcription: Callback when transcription completes
            on_recording: Callback when recording state changes
            on_transcribing: Callback when transcription state changes
            on_worker_done: Callback when worker finishes
        """
        self.config = config
        self._on_transcription = on_transcription
        self._on_recording = on_recording
        self._on_transcribing = on_transcribing
        self._on_worker_done = on_worker_done
        self._core: Optional[App] = None
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

    @property
    def core(self) -> Optional[App]:
        """Get the core app instance."""
        return self._core

    def start(self, run_in_thread: Callable[[Callable[[], None]], None]) -> None:
        """Start the worker.
        
        Args:
            run_in_thread: Function to run the worker loop in a thread
                          (e.g., page.run_thread)
        """
        self._running = True
        run_in_thread(self._worker_loop)
        self._start_monitor()

    def stop(self) -> None:
        """Stop the worker and cleanup."""
        self._running = False
        if self._core:
            self._core.stop()

    def _worker_loop(self) -> None:
        """Background worker that runs the core app."""
        try:
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
        finally:
            if self._on_worker_done:
                self._on_worker_done()

    def _start_monitor(self) -> None:
        """Start the Flet process monitor thread."""
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self._monitor_thread.start()

    def _monitor_loop(self) -> None:
        """Monitor Flet process and cleanup when closed.

        WORKAROUND: Flet doesn't reliably fire on_disconnect when the window
        is closed via the X button. This monitor thread polls for the Flet
        subprocess and triggers cleanup when it terminates.

        TODO: Remove when Flet fixes window close detection.
        """
        # Wait for Flet to start
        time.sleep(2)

        while self._running:
            time.sleep(1)
            try:
                if not self._is_flet_running():
                    log.info("Flet process gone, cleaning up...")
                    self.stop()
                    os._exit(0)
            except Exception:
                pass

    @staticmethod
    def _is_flet_running() -> bool:
        """Check if Flet subprocess is still running.

        Returns:
            True if Flet process is running, False otherwise.
        """
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq flet.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return "flet.exe" in result.stdout
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "flet/flet"],
                    capture_output=True,
                    timeout=5,
                )
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True  # Assume running if check fails
