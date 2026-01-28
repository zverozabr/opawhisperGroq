"""CLI entry point."""

import argparse
import os
import signal
import subprocess
import sys

from . import __version__
from .app import App
from .backend import detect_backend_type
from .config import Config
from .lock import acquire_lock, release_lock
from .logging import get_logger, setup_logging

log = get_logger()


def check_dependencies(backend_type: str) -> None:
    """Verify required system tools are installed."""
    if sys.platform == "darwin":
        required = [("rec", "brew install sox")]
    elif sys.platform == "win32":
        required = [("ffmpeg", "winget install ffmpeg")]
    elif backend_type == "wayland":
        required = [
            ("arecord", "sudo pacman -S alsa-utils"),
            ("wl-copy", "sudo pacman -S wl-clipboard"),
            ("ydotool", "sudo pacman -S ydotool"),
        ]
    else:  # x11
        required = [
            ("arecord", "sudo pacman -S alsa-utils"),
            ("xclip", "sudo pacman -S xclip"),
            ("xdotool", "sudo pacman -S xdotool"),
        ]

    # Check command existence
    if sys.platform == "win32":
        check_cmd = ["where"]
    else:
        check_cmd = ["which"]

    missing = []
    for cmd, install_hint in required:
        result = subprocess.run(
            [*check_cmd, cmd],
            capture_output=True,
        )
        if result.returncode != 0:
            missing.append((cmd, install_hint))

    if missing:
        log.error("Missing dependencies:")
        for cmd, install_hint in missing:
            log.error(f"  {cmd} - install: {install_hint}")
        sys.exit(1)


def has_display() -> bool:
    """Check if display is available."""
    return bool(
        os.environ.get("DISPLAY")
        or os.environ.get("WAYLAND_DISPLAY")
        or sys.platform == "darwin"
    )


def run_cli(config: Config) -> None:
    """Run in headless CLI mode."""
    backend_type = config.backend if config.backend != "auto" else detect_backend_type()

    log.info(f"SoupaWhisper v{__version__}")
    log.info(f"Backend: {backend_type}")
    check_dependencies(backend_type)

    log.info(f"Model: {config.model}")
    log.info(f"Language: {config.language}")

    app = App(config)

    def handle_sigint(*_):
        """Handle Ctrl+C gracefully by stopping the app."""
        log.info("Exiting...")
        app.stop()

    signal.signal(signal.SIGINT, handle_sigint)

    app.run()


def run_tui() -> None:
    """Run in TUI mode (default)."""
    from .tui import run_tui as tui_main

    tui_main()


def run_gui() -> None:
    """Run in legacy GUI mode (Flet) - DEPRECATED."""
    log.warning("GUI mode has been removed. Use TUI mode instead.")
    log.info("Starting TUI mode...")
    run_tui()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Voice dictation tool using Groq Whisper API"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Run with terminal user interface (default)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run with legacy graphical user interface (Flet)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without UI (CLI mode - hotkey only)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SoupaWhisper v{__version__}",
    )
    args = parser.parse_args()

    acquire_lock()  # Kills existing instance if any

    config = Config.load()
    setup_logging(debug=config.debug)

    # Validate config
    errors = config.validate()
    if errors:
        log.warning("Configuration warnings:")
        for error in errors:
            log.warning(f"  - {error}")

    try:
        if args.gui:
            run_gui()
        elif args.headless:
            run_cli(config)
        else:
            # Default: TUI mode
            run_tui()
    finally:
        release_lock()


if __name__ == "__main__":
    main()
