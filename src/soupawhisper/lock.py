"""Single instance lock."""

import atexit
import logging
import os
import signal
import subprocess
import time

from soupawhisper.constants import LOCK_FILE, ensure_dir

# Use basic logging here as setup_logging may not be called yet
log = logging.getLogger("soupawhisper")


def _kill_process_tree(pid: int) -> None:
    """Kill a process and all its children."""
    try:
        # Find all child processes
        result = subprocess.run(
            ["pgrep", "-P", str(pid)],
            capture_output=True,
            text=True,
        )
        child_pids = [int(p) for p in result.stdout.strip().split() if p]

        # Kill children first (recursively)
        for child_pid in child_pids:
            _kill_process_tree(child_pid)

        # Kill the process itself
        os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass


def acquire_lock() -> bool:
    """
    Acquire single instance lock, killing any existing instance.

    Returns True if lock acquired successfully.
    """
    ensure_dir(LOCK_FILE.parent)

    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)
            # Process exists - kill it and all children
            log.info(f"Stopping existing instance (PID {pid})...")
            _kill_process_tree(pid)

            # Wait for it to terminate (max 3 seconds)
            for _ in range(30):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except OSError:
                    break  # Process terminated
            else:
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        except (ValueError, OSError):
            pass  # Process not running or invalid PID

    LOCK_FILE.write_text(str(os.getpid()))
    atexit.register(release_lock)
    return True


def release_lock() -> None:
    """Release the lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError:
        pass
