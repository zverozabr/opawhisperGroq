"""Audio recording functionality."""

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioDevice:
    """Audio input device."""

    id: str  # Device identifier (e.g., "hw:0,0" or "default")
    name: str  # Human-readable name


def _get_record_command(output_path: str, device: str = "default") -> list[str]:
    """Get platform-specific audio record command.

    Args:
        output_path: Path to output WAV file
        device: Audio device ID

    Returns:
        Command list for subprocess
    """
    if sys.platform == "darwin":
        # macOS: use sox (install with `brew install sox`)
        cmd = [
            "rec",
            "-r", "16000",    # 16kHz sample rate
            "-c", "1",        # Mono
            "-b", "16",       # 16-bit
            output_path,
        ]
        # Note: sox on macOS uses different device naming
        return cmd

    if sys.platform == "win32":
        # Windows: use ffmpeg (install with `winget install ffmpeg` or `choco install ffmpeg`)
        cmd = [
            "ffmpeg",
            "-y",                    # Overwrite output
            "-f", "dshow",           # DirectShow input (Windows audio)
            "-i", f"audio={device}" if device != "default" else "audio=Microphone",
            "-ar", "16000",          # 16kHz sample rate
            "-ac", "1",              # Mono
            "-acodec", "pcm_s16le",  # 16-bit PCM
            output_path,
        ]
        return cmd

    # Linux: use arecord (ALSA)
    cmd = [
        "arecord",
        "-f", "S16_LE",   # 16-bit little-endian
        "-r", "16000",    # 16kHz sample rate
        "-c", "1",        # Mono
        "-t", "wav",
    ]

    # Add device if not default
    if device and device != "default":
        cmd.extend(["-D", device])

    cmd.append(output_path)
    return cmd


class AudioRecorder:
    """Records audio using platform-specific tools."""

    def __init__(self, device: str = "default"):
        """Initialize audio recorder.

        Args:
            device: Audio device ID to use for recording
        """
        self._process: subprocess.Popen | None = None
        self._temp_file: Path | None = None
        self._device = device

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

        command = _get_record_command(str(self._temp_file), self._device)
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

    @staticmethod
    def list_devices() -> list[AudioDevice]:
        """List available audio input devices.

        Returns:
            List of AudioDevice objects
        """
        devices: list[AudioDevice] = []

        if sys.platform == "darwin":
            # macOS: limited device enumeration
            # sox doesn't have easy device listing
            return devices

        if sys.platform == "win32":
            # Windows: use ffmpeg to list DirectShow devices
            try:
                result = subprocess.run(
                    ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # Parse stderr (ffmpeg outputs device list there)
                output = result.stderr
                in_audio_section = False
                for line in output.split("\n"):
                    if "DirectShow audio devices" in line:
                        in_audio_section = True
                        continue
                    if in_audio_section:
                        if "DirectShow video devices" in line:
                            break
                        # Look for device names in quotes
                        if '"' in line:
                            start = line.find('"') + 1
                            end = line.find('"', start)
                            if start > 0 and end > start:
                                device_name = line[start:end]
                                devices.append(AudioDevice(id=device_name, name=device_name))
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pass
            return devices

        # Linux: use arecord -L
        try:
            result = subprocess.run(
                ["arecord", "-L"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                current_id = None

                for line in lines:
                    if not line.startswith(" ") and not line.startswith("\t"):
                        # Device ID line
                        current_id = line.strip()
                    elif current_id and line.strip():
                        # Description line
                        name = line.strip()
                        # Filter for useful devices
                        if current_id in ("default", "pulse") or current_id.startswith(("hw:", "plughw:")):
                            devices.append(AudioDevice(id=current_id, name=name))
                        current_id = None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return devices
