#!/usr/bin/env python3
"""Diagnostic script to test audio recording from different devices."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path


def list_devices():
    """List all available audio devices."""
    print("=== Available Audio Devices ===")
    result = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
    )
    for line in result.stderr.split("\n"):
        if "AVFoundation" in line and ("[" in line):
            print(line)
    print()


def test_record(device_index: str, duration: int = 3):
    """Test recording from a specific device."""
    print(f"=== Recording from device :{device_index} for {duration}s ===")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-i", f":{device_index}",
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-t", str(duration),
        output_path,
    ]

    print(f"Command: {' '.join(cmd)}")
    print("Recording... (play some audio or speak)")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        # Filter out progress lines
        errors = [l for l in result.stderr.split("\n")
                  if "error" in l.lower() or "warning" in l.lower() or "Input" in l]
        if errors:
            print("Stderr:", "\n".join(errors[:5]))

    output = Path(output_path)
    if output.exists():
        size = output.stat().st_size
        print(f"Output file: {output_path}")
        print(f"File size: {size} bytes")

        if size < 1000:
            print("WARNING: File is very small - likely no audio captured!")
        else:
            print("SUCCESS: Audio captured!")

        # Get audio info
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", output_path],
            capture_output=True, text=True
        )
        for line in probe.stdout.split("\n"):
            if "duration" in line or "bit_rate" in line:
                print(f"  {line}")

        return output_path
    else:
        print("ERROR: No output file created")
        return None


def main():
    list_devices()

    if len(sys.argv) > 1:
        device = sys.argv[1]
    else:
        device = input("Enter device index to test (e.g., 1 for BY-V): ").strip()

    duration = 3
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])

    output = test_record(device, duration)

    if output:
        play = input("\nPlay recording? (y/n): ").strip().lower()
        if play == "y":
            subprocess.run(["afplay", output])

        Path(output).unlink()


if __name__ == "__main__":
    main()
