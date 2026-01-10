"""Audio recording functionality."""

import subprocess
import sys
import tempfile
from pathlib import Path


def _get_record_command(output_path: str) -> list[str]:
    """Get platform-specific audio record command."""
    if sys.platform == "darwin":
        # macOS: use sox (install with `brew install sox`)
        return [
            "rec",
            "-r", "16000",    # 16kHz sample rate
            "-c", "1",        # Mono
            "-b", "16",       # 16-bit
            output_path,
        ]
    # Linux: use arecord (ALSA)
    return [
        "arecord",
        "-f", "S16_LE",   # 16-bit little-endian
        "-r", "16000",    # 16kHz sample rate
        "-c", "1",        # Mono
        "-t", "wav",
        output_path,
    ]


class AudioRecorder:
    """Records audio using platform-specific tools."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._temp_file: Path | None = None

    @property
    def is_recording(self) -> bool:
        return self._process is not None

    @property
    def file_path(self) -> Path | None:
        return self._temp_file

    def start(self) -> None:
        """Start recording audio."""
        if self.is_recording:
            return

        temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp.close()
        self._temp_file = Path(temp.name)

        command = _get_record_command(str(self._temp_file))
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> Path | None:
        """Stop recording and return path to audio file."""
        if not self.is_recording:
            return None

        self._process.terminate()
        self._process.wait()
        self._process = None

        return self._temp_file

    def cleanup(self) -> None:
        """Remove temporary audio file."""
        if self._temp_file and self._temp_file.exists():
            self._temp_file.unlink()
            self._temp_file = None
