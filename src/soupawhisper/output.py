"""Output handling - clipboard and typing."""

import subprocess


def copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard using xclip."""
    process = subprocess.Popen(
        ["xclip", "-selection", "clipboard"],
        stdin=subprocess.PIPE,
    )
    process.communicate(input=text.encode())


def type_text(text: str) -> None:
    """Type text into active window using xdotool."""
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", text],
        check=False,
    )


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
