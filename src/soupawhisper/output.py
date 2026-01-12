"""Output handling - notifications."""

import subprocess

# Fixed notification ID for replacement (works on most DEs)
_NOTIFICATION_ID = 999888777


def notify(title: str, message: str, icon: str = "dialog-information", timeout_ms: int = 2000) -> None:
    """Show desktop notification, replacing any previous one.

    Uses multiple methods to ensure notification replacement:
    1. -r ID: Standard freedesktop replacement (libnotify 0.7.9+)
    2. -h string:x-canonical-private-synchronous: Ubuntu/Unity fallback
    """
    subprocess.run(
        [
            "notify-send",
            "-a", "SoupaWhisper",
            "-i", icon,
            "-t", str(timeout_ms),
            "-r", str(_NOTIFICATION_ID),  # Replace notification with this ID
            "-h", "string:x-canonical-private-synchronous:soupawhisper",  # Ubuntu fallback
            title,
            message,
        ],
        capture_output=True,
        check=False,
    )
