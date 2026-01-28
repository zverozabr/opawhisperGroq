#!/usr/bin/env python3
"""Benchmark all local Whisper models.

Tests transcription speed for all downloaded models.
Uses local paths for offline operation (no network requests).

Usage:
    uv run python scripts/benchmark_models.py
"""

import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from soupawhisper.providers.models import get_model_manager


@dataclass
class BenchmarkResult:
    """Result of a single model benchmark."""

    model_name: str
    size_mb: int
    transcription_time_ms: float
    audio_duration_sec: float
    realtime_factor: float
    text: str
    text_length: int


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds."""
    with wave.open(str(audio_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def benchmark_model_mlx(model_name: str, audio_path: Path, language: str = "ru") -> BenchmarkResult:
    """Benchmark a single MLX model."""
    import mlx_whisper

    manager = get_model_manager()
    model_info = manager.get_model_info(model_name)
    local_path = manager.get_model_path(model_name)

    if not local_path or not local_path.exists():
        raise ValueError(f"Model {model_name} not downloaded locally")

    audio_duration = get_audio_duration(audio_path)

    # Benchmark transcription
    start = time.perf_counter()
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=str(local_path),
        language=language,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    text = result.get("text", "").strip()
    realtime_factor = (audio_duration * 1000) / elapsed_ms if elapsed_ms > 0 else 0

    return BenchmarkResult(
        model_name=model_name,
        size_mb=model_info.size_mb if model_info else 0,
        transcription_time_ms=elapsed_ms,
        audio_duration_sec=audio_duration,
        realtime_factor=realtime_factor,
        text=text,
        text_length=len(text),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results as a table."""
    print()
    print("=" * 80)
    print("LOCAL MODEL BENCHMARK RESULTS")
    print("=" * 80)
    print()
    print(f"{'Model':<12} | {'Size':>8} | {'Time':>10} | {'RT Factor':>10} | {'Text Len':>8}")
    print("-" * 80)

    for r in results:
        print(
            f"{r.model_name:<12} | {r.size_mb:>6} MB | {r.transcription_time_ms:>8.0f} ms | "
            f"{r.realtime_factor:>9.1f}x | {r.text_length:>8}"
        )

    print("-" * 80)

    # Find fastest
    if results:
        fastest = min(results, key=lambda r: r.transcription_time_ms)
        print(f"\nFastest: {fastest.model_name} ({fastest.transcription_time_ms:.0f} ms, {fastest.realtime_factor:.1f}x realtime)")

    print()
    print("Transcription samples:")
    print("-" * 80)
    for r in results:
        print(f"{r.model_name}: {r.text[:60]}...")


def main():
    """Run benchmark for all downloaded models."""
    # Find test audio
    audio_path = Path(__file__).parent.parent / "tests" / "fixtures" / "test_russian_speech.wav"
    if not audio_path.exists():
        print(f"Error: Test audio not found: {audio_path}")
        sys.exit(1)

    print(f"Audio file: {audio_path}")
    print(f"Audio duration: {get_audio_duration(audio_path):.2f} seconds")

    manager = get_model_manager()
    downloaded = manager.list_downloaded()

    if not downloaded:
        print("No models downloaded. Run model download first.")
        sys.exit(1)

    print(f"\nDownloaded models: {', '.join(downloaded)}")
    print("\nBenchmarking... (this may take a few minutes)")

    results = []
    for model_name in downloaded:
        try:
            print(f"  Testing {model_name}...", end=" ", flush=True)
            result = benchmark_model_mlx(model_name, audio_path)
            results.append(result)
            print(f"{result.transcription_time_ms:.0f} ms ({result.realtime_factor:.1f}x)")
        except Exception as e:
            print(f"Error: {e}")

    # Sort by model size
    results.sort(key=lambda r: r.size_mb)

    print_results(results)


if __name__ == "__main__":
    main()
