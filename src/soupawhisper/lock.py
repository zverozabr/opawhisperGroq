"""Single instance lock."""

import atexit
import os
import sys
from pathlib import Path

LOCK_FILE = Path.home() / ".cache" / "soupawhisper.lock"


def acquire_lock() -> bool:
    """
    Acquire single instance lock.

    Returns True if lock acquired, False if another instance is running.
    """
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)
            return False  # Process exists
        except (ValueError, OSError):
            pass  # Process not running, stale lock

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
