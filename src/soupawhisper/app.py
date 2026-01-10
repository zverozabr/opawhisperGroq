"""Main application logic."""

import sys

from .audio import AudioRecorder
from .backend import DisplayBackend, create_backend
from .config import Config
from .output import notify
from .transcribe import transcribe, TranscriptionError


class App:
    """Voice dictation application."""

    def __init__(self, config: Config, backend: DisplayBackend | None = None):
        self.config = config
        self.recorder = AudioRecorder()
        self.backend = backend or create_backend(config.backend, config.typing_delay)

        if not config.api_key:
            print("ERROR: Groq API key not configured!")
            print("Add your API key to ~/.config/soupawhisper/config.ini")
            sys.exit(1)

    def _notify(self, title: str, message: str, icon: str = "dialog-information", timeout: int = 2000) -> None:
        if self.config.notifications:
            notify(title, message, icon, timeout)

    def _on_press(self) -> None:
        if self.recorder.is_recording:
            return

        self.recorder.start()
        print("Recording...")
        self._notify("Recording...", "Release key when done", "audio-input-microphone", 30000)

    def _on_release(self) -> None:
        if not self.recorder.is_recording:
            return

        audio_path = self.recorder.stop()
        if not audio_path:
            return

        print("Transcribing...")
        self._notify("Transcribing...", "Sending to Groq API", "emblem-synchronizing", 30000)

        try:
            text = transcribe(
                str(audio_path),
                self.config.api_key,
                self.config.model,
                self.config.language,
            )

            if text:
                self.backend.copy_to_clipboard(text)
                if self.config.auto_type:
                    self.backend.type_text(text)
                    if self.config.auto_enter:
                        self.backend.press_key("enter")
                print(f"Transcribed: {text}")
                preview = text[:100] + ("..." if len(text) > 100 else "")
                self._notify("Done!", preview, "emblem-ok-symbolic", 3000)
            else:
                print("No speech detected")
                self._notify("No speech", "Try speaking louder", "dialog-warning", 2000)

        except TranscriptionError as e:
            print(f"Error: {e}")
            self._notify("Error", str(e)[:50], "dialog-error", 3000)

        finally:
            self.recorder.cleanup()

    def run(self) -> None:
        """Start the application."""
        print(f"Ready! Hold [{self.config.hotkey}] to record.")
        print("Press Ctrl+C to quit.")

        self.backend.listen_hotkey(
            self.config.hotkey,
            self._on_press,
            self._on_release,
        )
