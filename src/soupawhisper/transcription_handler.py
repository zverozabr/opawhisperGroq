"""Transcription handling with proper separation of concerns."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .backend.base import DisplayBackend
from .config import Config
from .logging import get_logger
from .output import notify
from .providers import TranscriptionError, TranscriptionResult, get_provider
from .storage import DebugData, DebugStorage

log = get_logger()


def detect_hallucination(text: str, threshold: float = 0.7) -> bool:
    """Detect Whisper hallucination patterns (repetitive text).

    Whisper sometimes hallucinates when audio is unclear, producing
    repetitive patterns like "well well well well..." or "Peak Peak Peak...".

    Args:
        text: Transcription text to check
        threshold: Fraction threshold (0.7 = 70% same word triggers detection)

    Returns:
        True if text appears to be a hallucination
    """
    words = text.split()

    # Short text is fine
    if len(words) < 5:
        return False

    # Check for repetitive pattern
    counter = Counter(words)
    if not counter:
        return False

    most_common_word, count = counter.most_common(1)[0]

    # If one word is more than threshold of text, likely hallucination
    if count / len(words) > threshold:
        log.warning(f"Hallucination detected: '{most_common_word}' repeated {count}/{len(words)} times")
        return True

    return False


@dataclass
class TranscriptionContext:
    """Context for a single transcription operation."""

    audio_path: Path
    config: Config
    backend: DisplayBackend
    debug_storage: Optional[DebugStorage]
    on_complete: Optional[Callable[[str, str], None]] = None


class TranscriptionHandler:
    """Handles the transcription workflow.

    Responsibilities:
    - Call Groq API for transcription
    - Copy result to clipboard
    - Type text if enabled
    - Save debug data
    - Notify user
    """

    def __init__(self, config: Config):
        self._notifications_enabled = config.notifications

    def _notify(self, title: str, message: str, icon: str = "dialog-information", timeout: int = 2000) -> None:
        """Show desktop notification if enabled."""
        if self._notifications_enabled:
            notify(title, message, icon, timeout)

    def handle(self, ctx: TranscriptionContext) -> Optional[str]:
        """Process transcription request.

        Args:
            ctx: TranscriptionContext with all required data

        Returns:
            Transcribed text or None if failed
        """
        log.info("Transcribing...")
        # No notification for "Transcribing..." - menu bar indicator shows status

        try:
            result = self._transcribe(ctx)
            if not result.text:
                log.warning("No speech detected")
                # No notification for "No speech" - KISS
                return None

            # Check for hallucination (repetitive text)
            if detect_hallucination(result.text):
                log.warning("Transcription rejected: hallucination detected")
                self._notify("Warning", "Unclear audio, try again", "dialog-warning", 2000)
                return None

            self._process_result(ctx, result)
            return result.text

        except TranscriptionError as e:
            log.error(f"Transcription error: {e}")
            self._notify("Error", str(e)[:50], "dialog-error", 3000)  # Keep error notifications
            return None

    def _transcribe(self, ctx: TranscriptionContext) -> TranscriptionResult:
        """Call the transcription provider.

        Note: Re-reads config from disk to pick up changes made in UI.
        """
        from soupawhisper.config import Config

        # Re-read config to get latest provider settings from UI
        fresh_config = Config.load()
        provider = get_provider(fresh_config.active_provider)
        return provider.transcribe(str(ctx.audio_path), fresh_config.language)

    def _process_result(self, ctx: TranscriptionContext, result: TranscriptionResult) -> None:
        """Process successful transcription result."""
        text = result.text

        # Copy to clipboard
        ctx.backend.copy_to_clipboard(text)

        # Type text if enabled
        typed_text = ""
        typing_method = "none"
        if ctx.config.auto_type:
            typing_method = ctx.backend.type_text(text)
            typed_text = text
            if ctx.config.auto_enter:
                ctx.backend.press_key("enter")

        # Save debug data
        if ctx.debug_storage:
            debug_data = DebugData(
                text=text,
                clipboard_text=text,
                typed_text=typed_text,
                typing_method=typing_method,
            )
            ctx.debug_storage.save(
                ctx.audio_path,
                debug_data,
                result.raw_response,
            )

        # Log result (no notification - KISS, menu bar indicator sufficient)
        log.info(f"Transcribed: {text}")

        # Notify callback (for GUI)
        if ctx.on_complete:
            ctx.on_complete(text, ctx.config.language)
