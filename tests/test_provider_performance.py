"""Performance E2E tests for transcription providers.

Measures:
1. Transcription time for each provider (Groq, MLX, faster-whisper)
2. Provider switching time + model loading
3. Speed comparison between providers

Requirements:
- Groq API key in config
- mlx-whisper (macOS only)
- faster-whisper
- Test audio file in fixtures/

Run:
    uv run pytest tests/test_provider_performance.py -v -s --tb=short
    uv run pytest -m performance -v -s
"""

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from soupawhisper.config import CONFIG_PATH, Config
from soupawhisper.providers import (
    FasterWhisperProvider,
    MLXProvider,
    OpenAICompatibleProvider,
    ProviderConfig,
    load_providers_config,
)

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Performance test marker
pytestmark = pytest.mark.performance


@dataclass
class TranscriptionMetrics:
    """Metrics for a single transcription."""

    provider: str
    model: str
    audio_duration_sec: float
    transcription_time_ms: float
    text_length: int
    realtime_factor: float = field(init=False)

    def __post_init__(self):
        """Calculate realtime factor."""
        if self.transcription_time_ms > 0:
            self.realtime_factor = (
                self.audio_duration_sec * 1000 / self.transcription_time_ms
            )
        else:
            self.realtime_factor = 0.0

    def __str__(self) -> str:
        return (
            f"{self.provider:20} | {self.transcription_time_ms:8.0f} ms | "
            f"{self.realtime_factor:6.1f}x | {self.text_length:4} chars"
        )


@dataclass
class SwitchingMetrics:
    """Metrics for provider switching."""

    from_provider: str
    to_provider: str
    switch_time_ms: float
    first_transcription_time_ms: float

    def __str__(self) -> str:
        return (
            f"{self.from_provider} -> {self.to_provider}: "
            f"switch={self.switch_time_ms:.0f}ms, "
            f"first_transcribe={self.first_transcription_time_ms:.0f}ms"
        )


class MetricsCollector:
    """Collects and reports performance metrics."""

    def __init__(self):
        self.transcription_metrics: list[TranscriptionMetrics] = []
        self.switching_metrics: list[SwitchingMetrics] = []

    def add_transcription(self, metrics: TranscriptionMetrics) -> None:
        self.transcription_metrics.append(metrics)

    def add_switching(self, metrics: SwitchingMetrics) -> None:
        self.switching_metrics.append(metrics)

    def print_report(self) -> None:
        """Print performance report."""
        print("\n" + "=" * 70)
        print("PROVIDER PERFORMANCE REPORT")
        print("=" * 70)

        if self.transcription_metrics:
            print("\nTranscription Times:")
            print("-" * 70)
            print(f"{'Provider':20} | {'Time':>10} | {'RT Factor':>8} | {'Text'}")
            print("-" * 70)
            for m in self.transcription_metrics:
                print(m)

        if self.switching_metrics:
            print("\nProvider Switching Times:")
            print("-" * 70)
            for m in self.switching_metrics:
                print(m)

        print("=" * 70)


# Global metrics collector
_collector = MetricsCollector()


def get_api_key() -> str | None:
    """Get Groq API key from environment or config."""
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key

    try:
        config = load_providers_config()
        groq_config = config.get("providers", {}).get("groq", {})
        key = groq_config.get("api_key", "")
        if key and key != "your_groq_api_key_here":
            return key
    except Exception:
        key = None

    try:
        config = Config.load(CONFIG_PATH)
        if config.api_key and config.api_key != "your_groq_api_key_here":
            return config.api_key
    except Exception:
        key = None

    return None


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using wave module."""
    import wave

    with wave.open(str(audio_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


@pytest.fixture
def api_key():
    """Get API key or skip test."""
    key = get_api_key()
    if not key:
        pytest.skip("Groq API key not available")
    return key


@pytest.fixture
def russian_speech_audio():
    """Path to Russian speech test audio."""
    path = FIXTURES_DIR / "test_russian_speech.wav"
    if not path.exists():
        pytest.skip(f"Test audio not found: {path}")
    return path


@pytest.fixture
def audio_duration(russian_speech_audio) -> float:
    """Get audio duration in seconds."""
    return get_audio_duration(russian_speech_audio)


class TestGroqPerformance:
    """Performance tests for Groq API provider."""

    @pytest.mark.performance
    def test_groq_transcription_speed(
        self, api_key, russian_speech_audio, audio_duration
    ):
        """Measure Groq API transcription speed."""
        provider = OpenAICompatibleProvider(
            ProviderConfig(
                name="groq",
                type="openai_compatible",
                api_key=api_key,
                url="https://api.groq.com/openai/v1/audio/transcriptions",
                model="whisper-large-v3",
            )
        )

        # Measure transcription time
        start = time.perf_counter()
        result = provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.text, "Transcription should return text"

        metrics = TranscriptionMetrics(
            provider="groq",
            model="whisper-large-v3",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms,
            text_length=len(result.text),
        )

        _collector.add_transcription(metrics)
        print(f"\n[GROQ] {metrics}")

        # Assert reasonable performance (should be faster than realtime)
        assert metrics.realtime_factor > 1.0, "Groq should be faster than realtime"


class TestMLXPerformance:
    """Performance tests for MLX local provider (macOS only)."""

    @pytest.mark.skipif(sys.platform != "darwin", reason="MLX requires macOS")
    @pytest.mark.performance
    def test_mlx_transcription_speed(self, russian_speech_audio, audio_duration):
        """Measure MLX transcription speed including model load."""
        try:
            import mlx_whisper  # noqa: F401
        except ImportError:
            pytest.skip("mlx-whisper not installed")

        provider = MLXProvider(
            ProviderConfig(
                name="local-mlx",
                type="mlx",
                model="mlx-community/whisper-base-mlx",
            )
        )

        # First transcription includes model loading
        start = time.perf_counter()
        result = provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.text, "Transcription should return text"

        metrics = TranscriptionMetrics(
            provider="local-mlx (base)",
            model="whisper-base-mlx",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms,
            text_length=len(result.text),
        )

        _collector.add_transcription(metrics)
        print(f"\n[MLX] {metrics}")

        # Second transcription (model already loaded)
        start = time.perf_counter()
        result2 = provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms_2 = (time.perf_counter() - start) * 1000

        metrics2 = TranscriptionMetrics(
            provider="local-mlx (cached)",
            model="whisper-base-mlx",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms_2,
            text_length=len(result2.text),
        )

        _collector.add_transcription(metrics2)
        print(f"[MLX cached] {metrics2}")


class TestFasterWhisperPerformance:
    """Performance tests for faster-whisper local provider."""

    @pytest.mark.performance
    def test_faster_whisper_speed(self, russian_speech_audio, audio_duration):
        """Measure faster-whisper transcription speed."""
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            pytest.skip("faster-whisper not installed")

        provider = FasterWhisperProvider(
            ProviderConfig(
                name="local-cpu",
                type="faster_whisper",
                model="base",
            )
        )

        # First transcription includes model loading
        start = time.perf_counter()
        result = provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.text, "Transcription should return text"

        metrics = TranscriptionMetrics(
            provider="local-cpu (base)",
            model="base",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms,
            text_length=len(result.text),
        )

        _collector.add_transcription(metrics)
        print(f"\n[faster-whisper] {metrics}")

        # Second transcription (model cached)
        start = time.perf_counter()
        result2 = provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms_2 = (time.perf_counter() - start) * 1000

        metrics2 = TranscriptionMetrics(
            provider="local-cpu (cached)",
            model="base",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms_2,
            text_length=len(result2.text),
        )

        _collector.add_transcription(metrics2)
        print(f"[faster-whisper cached] {metrics2}")


class TestProviderSwitching:
    """Test provider switching performance."""

    @pytest.mark.performance
    def test_switch_groq_to_local(self, api_key, russian_speech_audio, audio_duration):
        """Measure time to switch from Groq to local provider."""
        # Start with Groq
        groq_provider = OpenAICompatibleProvider(
            ProviderConfig(
                name="groq",
                type="openai_compatible",
                api_key=api_key,
                url="https://api.groq.com/openai/v1/audio/transcriptions",
                model="whisper-large-v3",
            )
        )

        # Transcribe with Groq first
        groq_provider.transcribe(russian_speech_audio, language="ru")

        # Check if faster-whisper is available
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            pytest.skip("faster-whisper not installed")

        # Switch to local provider and measure
        start = time.perf_counter()
        local_provider = FasterWhisperProvider(
            ProviderConfig(name="local-cpu", type="faster_whisper", model="base")
        )
        switch_time_ms = (time.perf_counter() - start) * 1000

        # First transcription after switch
        start = time.perf_counter()
        result = local_provider.transcribe(russian_speech_audio, language="ru")
        first_transcribe_ms = (time.perf_counter() - start) * 1000

        assert result.text

        metrics = SwitchingMetrics(
            from_provider="groq",
            to_provider="local-cpu",
            switch_time_ms=switch_time_ms,
            first_transcription_time_ms=first_transcribe_ms,
        )

        _collector.add_switching(metrics)
        print(f"\n[SWITCH] {metrics}")


class TestProviderComparison:
    """Compare all available providers."""

    @pytest.mark.performance
    def test_compare_all_providers(
        self, api_key, russian_speech_audio, audio_duration
    ):
        """Compare transcription speed across all available providers."""
        results = []

        # 1. Groq
        print("\n--- Testing Groq ---")
        groq_provider = OpenAICompatibleProvider(
            ProviderConfig(
                name="groq",
                type="openai_compatible",
                api_key=api_key,
                url="https://api.groq.com/openai/v1/audio/transcriptions",
                model="whisper-large-v3",
            )
        )

        start = time.perf_counter()
        result = groq_provider.transcribe(russian_speech_audio, language="ru")
        elapsed_ms = (time.perf_counter() - start) * 1000

        groq_metrics = TranscriptionMetrics(
            provider="groq",
            model="whisper-large-v3",
            audio_duration_sec=audio_duration,
            transcription_time_ms=elapsed_ms,
            text_length=len(result.text),
        )
        results.append(("groq", result.text, groq_metrics))
        _collector.add_transcription(groq_metrics)

        # 2. MLX (if available)
        if sys.platform == "darwin":
            try:
                import mlx_whisper  # noqa: F401

                print("--- Testing MLX ---")
                mlx_provider = MLXProvider(
                    ProviderConfig(
                        name="local-mlx",
                        type="mlx",
                        model="mlx-community/whisper-base-mlx",
                    )
                )

                start = time.perf_counter()
                result = mlx_provider.transcribe(russian_speech_audio, language="ru")
                elapsed_ms = (time.perf_counter() - start) * 1000

                mlx_metrics = TranscriptionMetrics(
                    provider="local-mlx",
                    model="whisper-base-mlx",
                    audio_duration_sec=audio_duration,
                    transcription_time_ms=elapsed_ms,
                    text_length=len(result.text),
                )
                results.append(("mlx", result.text, mlx_metrics))
                _collector.add_transcription(mlx_metrics)
            except ImportError:
                print("MLX not available, skipping")

        # 3. faster-whisper (if available)
        try:
            import faster_whisper  # noqa: F401

            print("--- Testing faster-whisper ---")
            fw_provider = FasterWhisperProvider(
                ProviderConfig(name="local-cpu", type="faster_whisper", model="base")
            )

            start = time.perf_counter()
            result = fw_provider.transcribe(russian_speech_audio, language="ru")
            elapsed_ms = (time.perf_counter() - start) * 1000

            fw_metrics = TranscriptionMetrics(
                provider="local-cpu",
                model="base",
                audio_duration_sec=audio_duration,
                transcription_time_ms=elapsed_ms,
                text_length=len(result.text),
            )
            results.append(("faster-whisper", result.text, fw_metrics))
            _collector.add_transcription(fw_metrics)
        except ImportError:
            print("faster-whisper not available, skipping")

        # Print comparison report
        _collector.print_report()

        # Assertions
        assert len(results) >= 1, "At least one provider should work"

        # Print transcription texts for comparison
        print("\nTranscription Results:")
        print("-" * 70)
        for name, text, _ in results:
            print(f"{name}: {text[:80]}...")


@pytest.fixture(scope="session", autouse=True)
def print_final_report():
    """Print final report at end of session."""
    yield
    if _collector.transcription_metrics or _collector.switching_metrics:
        _collector.print_report()
