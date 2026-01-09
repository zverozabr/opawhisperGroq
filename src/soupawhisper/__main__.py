"""CLI entry point."""

import os
import signal
import subprocess
import sys

from . import __version__
from .app import App
from .config import Config
from .lock import acquire_lock, release_lock


def check_dependencies() -> None:
    """Verify required system tools are installed."""
    required = [
        ("arecord", "alsa-utils"),
        ("xclip", "xclip"),
        ("xdotool", "xdotool"),
    ]

    missing = [
        (cmd, pkg)
        for cmd, pkg in required
        if subprocess.run(["which", cmd], capture_output=True).returncode != 0
    ]

    if missing:
        print("Missing dependencies:")
        for cmd, pkg in missing:
            print(f"  {cmd} - install: sudo pacman -S {pkg}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    if not acquire_lock():
        print("SoupaWhisper is already running!")
        sys.exit(1)

    print(f"SoupaWhisper v{__version__}")
    check_dependencies()

    config = Config.load()
    print(f"Model: {config.model}")
    print(f"Language: {config.language}")

    def handle_sigint(*_):
        """Handle Ctrl+C gracefully with os._exit to avoid pynput thread issues."""
        print("\nExiting...")
        release_lock()
        os._exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    App(config).run()


if __name__ == "__main__":
    main()
