"""Output handling - notifications."""

import subprocess


def notify(title: str, message: str, icon: str = "dialog-information", timeout_ms: int = 2000) -> None:
    """Show desktop notification."""
    subprocess.run(
        [
            "notify-send",
            "-a", "SoupaWhisper",
            "-i", icon,
            "-t", str(timeout_ms),
            "-h", "string:x-canonical-private-synchronous:soupawhisper",
            title,
            message,
        ],
        capture_output=True,
        check=False,
    )
