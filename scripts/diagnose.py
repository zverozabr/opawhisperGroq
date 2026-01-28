#!/usr/bin/env python3
"""Diagnostic script for SoupaWhisper audio and transcription."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from soupawhisper.config import Config
from soupawhisper.audio import AudioRecorder
from soupawhisper.providers import OpenAICompatibleProvider, ProviderConfig, TranscriptionError


def test_audio_devices():
    """List available audio devices."""
    print("=" * 50)
    print("AUDIO DEVICES")
    print("=" * 50)

    devices = AudioRecorder.list_devices()
    if not devices:
        print("No devices found via arecord -L")
    else:
        for d in devices:
            print(f"  {d.id}: {d.name}")

    # Also run arecord -l for hardware list
    print("\nHardware devices (arecord -l):")
    try:
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        print(result.stdout or "  (none)")
        if result.stderr:
            print(f"  Errors: {result.stderr}")
    except Exception as e:
        print(f"  Error: {e}")


def test_recording(duration: int = 3, device: str = "default"):
    """Test audio recording."""
    print("\n" + "=" * 50)
    print(f"RECORDING TEST ({duration}s, device={device})")
    print("=" * 50)

    recorder = AudioRecorder(device=device)

    print(f"Recording for {duration} seconds... Speak now!")
    recorder.start()
    time.sleep(duration)
    audio_path = recorder.stop()

    if not audio_path or not audio_path.exists():
        print("ERROR: No audio file created!")
        return None

    size = audio_path.stat().st_size
    print(f"Audio file: {audio_path}")
    print(f"File size: {size} bytes")

    # Check if file has actual audio (not just header)
    if size < 1000:
        print("WARNING: File too small - microphone may not be working")
    elif size < 5000:
        print("WARNING: File is small - check if microphone is picking up sound")
    else:
        print("OK: Audio file size looks reasonable")

    # Play info about the file
    try:
        result = subprocess.run(
            ["file", str(audio_path)],
            capture_output=True, text=True
        )
        print(f"File type: {result.stdout.strip()}")
    except Exception:
        pass

    return audio_path


def test_transcription(audio_path: Path):
    """Test transcription with audio file."""
    print("\n" + "=" * 50)
    print("TRANSCRIPTION TEST")
    print("=" * 50)

    config = Config.load()

    if not config.api_key:
        print("ERROR: No API key configured!")
        print("Add your Groq API key to ~/.config/soupawhisper/config.ini")
        return

    print(f"API Key: {config.api_key[:8]}...{config.api_key[-4:]}")
    print(f"Model: {config.model}")
    print(f"Language: {config.language}")

    print("\nSending to Groq API...")
    try:
        provider_config = ProviderConfig(
            name="groq",
            type="openai_compatible",
            url="https://api.groq.com/openai/v1/audio/transcriptions",
            api_key=config.api_key,
            model=config.model,
        )
        provider = OpenAICompatibleProvider(provider_config)
        result = provider.transcribe(str(audio_path), config.language)
        print(f"\nRESULT: '{result.text}'")
        if not result.text:
            print("WARNING: Empty result - either silent audio or API issue")
        else:
            print("OK: Transcription successful")
    except TranscriptionError as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")


def test_config():
    """Show current configuration."""
    print("=" * 50)
    print("CONFIGURATION")
    print("=" * 50)

    config = Config.load()
    print(f"  Language: {config.language}")
    print(f"  Hotkey: {config.hotkey}")
    print(f"  Audio device: {config.audio_device}")
    print(f"  Auto-type: {config.auto_type}")
    print(f"  Auto-enter: {config.auto_enter}")
    print(f"  Typing delay: {config.typing_delay}ms")
    print(f"  Backend: {config.backend}")
    print(f"  Notifications: {config.notifications}")


def main():
    print("SoupaWhisper Diagnostic Tool")
    print("=" * 50)

    test_config()
    test_audio_devices()

    # Record and transcribe
    audio_path = test_recording(duration=3)
    if audio_path:
        test_transcription(audio_path)
        # Cleanup
        try:
            audio_path.unlink()
        except Exception:
            pass

    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)


if __name__ == "__main__":
    main()
