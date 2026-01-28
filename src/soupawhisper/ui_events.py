"""UI event handling protocols.

SOLID - Interface Segregation:
Small, focused protocols for UI event callbacks.
Shared by both GUI (Flet) and TUI (Textual) implementations.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class RecordingHandler(Protocol):
    """Protocol for handling recording state changes."""

    def on_recording_changed(self, is_recording: bool) -> None:
        """Called when recording state changes.

        Args:
            is_recording: True if recording started, False if stopped.
        """
        ...


@runtime_checkable
class TranscriptionHandler(Protocol):
    """Protocol for handling transcription events."""

    def on_transcription_complete(self, text: str, language: str) -> None:
        """Called when transcription completes.

        Args:
            text: Transcribed text.
            language: Detected language code.
        """
        ...

    def on_transcribing_changed(self, is_transcribing: bool) -> None:
        """Called when transcription state changes.

        Args:
            is_transcribing: True if transcription started, False if completed.
        """
        ...


@runtime_checkable
class ErrorHandler(Protocol):
    """Protocol for handling errors."""

    def on_error(self, message: str) -> None:
        """Called when an error occurs.

        Args:
            message: Error message to display.
        """
        ...


@runtime_checkable
class UIEventHandler(RecordingHandler, TranscriptionHandler, ErrorHandler, Protocol):
    """Combined protocol for all UI events.

    Implementations can choose to implement all or just the protocols they need.
    """

    pass
