"""CLI entry point."""

import argparse
import os
import signal
import subprocess
import sys

from . import __version__
from .app import App, validate_config
from .backend import detect_backend_type
from .config import Config
from .lock import acquire_lock, release_lock
from .logging import get_logger, setup_logging

log = get_logger()


def check_dependencies(backend_type: str) -> None:
    """Verify required system tools are installed."""
    if sys.platform == "darwin":
        required = [("rec", "brew install sox")]
        optional = []
    elif sys.platform == "win32":
        required = [("ffmpeg", "winget install ffmpeg")]
        optional = []
    elif backend_type == "wayland":
        # Wayland: only audio and clipboard are required
        # Typing tools (wtype/ydotool) are optional - falls back to clipboard
        required = [
            ("arecord", "sudo pacman -S alsa-utils"),
            ("wl-copy", "sudo pacman -S wl-clipboard"),
        ]
        optional = [
            ("wtype", "For auto-typing: yay -S wtype"),
            ("ydotool", "Alternative: sudo pacman -S ydotool"),
        ]
    else:  # x11
        required = [
            ("arecord", "sudo pacman -S alsa-utils"),
            ("xclip", "sudo pacman -S xclip"),
            ("xdotool", "sudo pacman -S xdotool"),
        ]
        optional = []

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

    # Check optional dependencies (warn but don't exit)
    if optional:
        missing_optional = []
        for cmd, hint in optional:
            result = subprocess.run([*check_cmd, cmd], capture_output=True)
            if result.returncode != 0:
                missing_optional.append((cmd, hint))
        
        # Warn if no typing tool available (Wayland)
        if backend_type == "wayland" and len(missing_optional) == len(optional):
            log.warning("No typing tool found (wtype/ydotool). Text will be copied to clipboard only.")
            log.warning("Install wtype for auto-typing: yay -S wtype")


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

    errors = validate_config(config)
    if errors:
        for error in errors:
            log.error(error)
        log.error("Add your API key to ~/.config/soupawhisper/config.ini")
        sys.exit(1)

    app = App(config)

    def handle_sigint(*_):
        """Handle Ctrl+C gracefully by stopping the app."""
        log.info("Exiting...")
        app.stop()

    signal.signal(signal.SIGINT, handle_sigint)

    app.run()


def run_tui(config: Config) -> None:
    """Run in TUI mode (default)."""
    from .tui.app import TUIApp

    TUIApp(config=config).run()


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
        "--headless",
        action="store_true",
        help="Run without UI (CLI mode - hotkey only)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SoupaWhisper v{__version__}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and save recordings",
    )
    args = parser.parse_args()

    acquire_lock()  # Kills existing instance if any

    config = Config.load()
    # Override debug from CLI if specified
    if args.debug:
        config.debug = True

    # Setup logging - write to file in debug mode
    log_file = None
    if config.debug:
        from soupawhisper.constants import LOGS_DIR, ensure_dir
        ensure_dir(LOGS_DIR)
        log_file = LOGS_DIR / "soupawhisper.log"

    # Determine if TUI mode (no console logs to avoid display corruption)
    is_tui_mode = not args.headless

    setup_logging(debug=config.debug, log_file=log_file, tui_mode=is_tui_mode)

    if config.debug and log_file:
        log.info(f"Debug mode enabled. Logs: {log_file}")

    # Validate config
    errors = config.validate()
    if errors:
        log.warning("Configuration warnings:")
        for error in errors:
            log.warning(f"  - {error}")

    try:
        if args.headless:
            run_cli(config)
        else:
            # Default: TUI mode
            run_tui(config)
    finally:
        release_lock()


if __name__ == "__main__":
    main()
