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


@dataclass
class DeviceResolver:
    """Resolves which audio device to use for recording.

    Handles: default selection, fallback when device missing, auto-reconnection.

    Single Responsibility: Device selection logic only.

    Performance: Uses cached device list to avoid latency on recording start.
    Cache is refreshed after each recording stops (in background).
    """

    preferred_device: str = "default"  # User's saved preference from config

    # Class-level cache shared across instances
    _cached_devices: list = None  # type: ignore
    _cache_valid: bool = False

    def resolve(self) -> str:
        """Get device ID to use for recording.

        Uses cached device list for zero latency.
        If no cache, falls back to simple logic without ffmpeg call.

        Returns:
            Device ID to use for recording
        """
        # "default" means use first available (device 0)
        if self.preferred_device == "default":
            if DeviceResolver._cache_valid and DeviceResolver._cached_devices:
                return DeviceResolver._cached_devices[0].id
            return "0"  # Fallback if no cache

        # Use cached devices if available
        if DeviceResolver._cache_valid and DeviceResolver._cached_devices:
            device_ids = {d.id for d in DeviceResolver._cached_devices}
            if self.preferred_device in device_ids:
                return self.preferred_device
            # Preferred device missing -> fallback
            return DeviceResolver._cached_devices[0].id if DeviceResolver._cached_devices else "0"

        # No cache - trust user's choice (ffmpeg will error if wrong)
        return self.preferred_device

    def is_preferred_available(self) -> bool:
        """Check if preferred device is currently connected.

        Returns:
            True if device is available, False otherwise
        """
        if self.preferred_device == "default":
            return True
        if DeviceResolver._cache_valid and DeviceResolver._cached_devices:
            return any(d.id == self.preferred_device for d in DeviceResolver._cached_devices)
        return True  # Assume available if no cache

    @classmethod
    def refresh_cache(cls) -> None:
        """Refresh device cache (call after recording stops)."""
        import threading

        def _refresh():
            try:
                cls._cached_devices = AudioRecorder.list_devices()
                cls._cache_valid = True
            except Exception:
                pass

        # Run in background to not block
        thread = threading.Thread(target=_refresh, daemon=True)
        thread.start()

    @classmethod
    def invalidate_cache(cls) -> None:
        """Invalidate cache (call when user changes device in settings)."""
        cls._cache_valid = False


def _get_record_command(output_path: str, device: str = "default") -> list[str]:
    """Get platform-specific audio record command.

    Args:
        output_path: Path to output WAV file
        device: Audio device ID

    Returns:
        Command list for subprocess
    """
    if sys.platform == "darwin":
        # macOS: use ffmpeg with AVFoundation
        # Device format: ":INDEX" where INDEX is audio device number from ffmpeg -list_devices
        audio_input = f":{device}" if device and device != "default" else ":0"
        cmd = [
            "ffmpeg",
            "-y",                    # Overwrite output
            "-f", "avfoundation",    # macOS audio/video framework
            "-i", audio_input,       # Audio device index
            "-ar", "16000",          # 16kHz sample rate
            "-ac", "1",              # Mono
            "-acodec", "pcm_s16le",  # 16-bit PCM
            output_path,
        ]
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
            device: Audio device ID (user's preferred device from config)
        """
        self._process: subprocess.Popen | None = None
        self._temp_file: Path | None = None
        self._device = device
        self._resolver = DeviceResolver(preferred_device=device)
        self.last_error: str | None = None
        self.last_stderr: str | None = None
        self.actual_device: str | None = None  # Device used for current recording

    @property
    def is_recording(self) -> bool:
        return self._process is not None

    @property
    def file_path(self) -> Path | None:
        return self._temp_file

    def start(self) -> None:
        """Start recording audio.

        Resolves device on EVERY recording start to handle:
        - Device disconnection (fallback to default)
        - Device reconnection (switch back to preferred)
        """
        if self.is_recording:
            return

        # Clear previous stderr on new recording
        self.last_stderr = None

        # Resolve device (checks availability, handles fallback/reconnection)
        self.actual_device = self._resolver.resolve()

        temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp.close()
        self._temp_file = Path(temp.name)

        command = _get_record_command(str(self._temp_file), self.actual_device)
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def stop(self) -> Path | None:
        """Stop recording and return path to audio file."""
        if not self.is_recording:
            return None

        # Send SIGINT to ffmpeg for graceful shutdown (writes proper WAV header)
        self._process.terminate()

        # Capture stderr using communicate with timeout
        try:
            _, stderr = self._process.communicate(timeout=2)
            if stderr:
                self.last_stderr = stderr.decode(errors="ignore")
        except subprocess.TimeoutExpired:
            # Process didn't finish in time, force kill
            self._process.kill()
            self._process.wait()

        self._process = None

        # Refresh device cache in background for next recording
        DeviceResolver.refresh_cache()

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
            # macOS: use ffmpeg to list AVFoundation devices
            try:
                result = subprocess.run(
                    ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # Parse stderr (ffmpeg outputs device list there)
                output = result.stderr
                in_audio_section = False
                for line in output.split("\n"):
                    if "AVFoundation audio devices" in line:
                        in_audio_section = True
                        continue
                    if in_audio_section:
                        # Lines look like: [AVFoundation ...] [0] Device Name
                        if "] [" in line:
                            # Extract device index and name
                            idx_start = line.rfind("] [") + 3
                            idx_end = line.find("]", idx_start)
                            name_start = idx_end + 2
                            if idx_start > 2 and idx_end > idx_start:
                                device_id = line[idx_start:idx_end]
                                device_name = line[name_start:].strip()
                                if device_id.isdigit() and device_name:
                                    devices.append(AudioDevice(id=device_id, name=device_name))
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pass
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
