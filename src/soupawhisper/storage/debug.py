"""Debug storage for saving last N recordings."""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from soupawhisper.constants import DEBUG_DIR, ensure_dir

MAX_RECORDINGS = 3


@dataclass
class DebugData:
    """Debug data for a single transcription."""

    text: str  # Recognized text from API
    clipboard_text: str  # Text copied to clipboard
    typed_text: str  # Text typed into window (may differ if auto_type disabled)
    typing_method: str  # Method used: "xdotool", "wtype", "ydotool", "clipboard", "pynput", "none"


@dataclass
class DebugRecord:
    """Single debug recording."""

    timestamp: str  # ISO format YYYYMMDD_HHMMSS
    audio_path: Path
    text: str
    clipboard_text: str
    typed_text: str
    typing_method: str
    response: dict[str, Any]


class DebugStorage:
    """Manages debug recordings with automatic rotation."""

    def __init__(self, debug_dir: Path = DEBUG_DIR):
        self.debug_dir = debug_dir
        ensure_dir(self.debug_dir)

    def save(
        self,
        audio_path: Path,
        debug_data: DebugData,
        raw_response: dict[str, Any],
    ) -> Path:
        """Save debug recording.

        Args:
            audio_path: Path to audio file (will be copied)
            debug_data: Debug data with text, clipboard, typed info
            raw_response: Full API response JSON

        Returns:
            Path to debug recording directory
        """
        # Create timestamped directory (with microseconds for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        record_dir = ensure_dir(self.debug_dir / timestamp)

        # Copy audio file
        audio_dest = record_dir / "audio.wav"
        shutil.copy2(audio_path, audio_dest)

        # Save recognized text
        text_path = record_dir / "text.txt"
        text_path.write_text(debug_data.text, encoding="utf-8")

        # Save clipboard text
        clipboard_path = record_dir / "clipboard.txt"
        clipboard_path.write_text(debug_data.clipboard_text, encoding="utf-8")

        # Save typed text with method info
        typed_path = record_dir / "typed.txt"
        typed_content = f"Method: {debug_data.typing_method}\n\n{debug_data.typed_text}"
        typed_path.write_text(typed_content, encoding="utf-8")

        # Save full response
        response_path = record_dir / "response.json"
        response_path.write_text(
            json.dumps(raw_response, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Rotate old recordings
        self._rotate()

        return record_dir

    def _rotate(self) -> None:
        """Keep only MAX_RECORDINGS most recent."""
        # Get all recording directories sorted by name (timestamp)
        dirs = sorted(
            [d for d in self.debug_dir.iterdir() if d.is_dir()],
            key=lambda d: d.name,
            reverse=True,  # Newest first
        )

        # Remove old ones
        for old_dir in dirs[MAX_RECORDINGS:]:
            shutil.rmtree(old_dir)

    def list_recordings(self) -> list[DebugRecord]:
        """List all debug recordings."""
        records = []
        for record_dir in sorted(self.debug_dir.iterdir(), reverse=True):
            if not record_dir.is_dir():
                continue

            audio_path = record_dir / "audio.wav"
            text_path = record_dir / "text.txt"
            clipboard_path = record_dir / "clipboard.txt"
            typed_path = record_dir / "typed.txt"
            response_path = record_dir / "response.json"

            if not audio_path.exists() or not response_path.exists():
                continue

            # Parse typed.txt to extract method and text
            typed_content = ""
            typing_method = "unknown"
            if typed_path.exists():
                typed_raw = typed_path.read_text(encoding="utf-8")
                lines = typed_raw.split("\n", 2)
                if lines and lines[0].startswith("Method: "):
                    typing_method = lines[0][8:]
                    typed_content = lines[2] if len(lines) > 2 else ""
                else:
                    typed_content = typed_raw

            records.append(
                DebugRecord(
                    timestamp=record_dir.name,
                    audio_path=audio_path,
                    text=text_path.read_text(encoding="utf-8") if text_path.exists() else "",
                    clipboard_text=clipboard_path.read_text(encoding="utf-8") if clipboard_path.exists() else "",
                    typed_text=typed_content,
                    typing_method=typing_method,
                    response=json.loads(response_path.read_text(encoding="utf-8")),
                )
            )

        return records[:MAX_RECORDINGS]

    def clear(self) -> None:
        """Delete all debug recordings."""
        for item in self.debug_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
