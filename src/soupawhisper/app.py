"""Main application logic."""

import sys
from pynput import keyboard

from .audio import AudioRecorder
from .config import Config
from .output import copy_to_clipboard, notify, type_text
from .transcribe import transcribe, TranscriptionError


def get_hotkey(key_name: str) -> keyboard.Key | keyboard.KeyCode:
    """Map key name string to pynput key."""
    key_name = key_name.lower()
    if hasattr(keyboard.Key, key_name):
        return getattr(keyboard.Key, key_name)
    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name)
    return keyboard.Key.f12


class App:
    """Voice dictation application."""

    def __init__(self, config: Config):
        self.config = config
        self.recorder = AudioRecorder()
        self.hotkey = get_hotkey(config.hotkey)

        if not config.api_key:
            print("ERROR: Groq API key not configured!")
            print("Add your API key to ~/.config/soupawhisper/config.ini")
            sys.exit(1)

    def _notify(self, title: str, message: str, icon: str = "dialog-information", timeout: int = 2000) -> None:
        if self.config.notifications:
            notify(title, message, icon, timeout)

    def _on_press(self, key: keyboard.Key) -> None:
        if key != self.hotkey or self.recorder.is_recording:
            return

        self.recorder.start()
        print("Recording...")
        self._notify("Recording...", "Release key when done", "audio-input-microphone", 30000)

    def _on_release(self, key: keyboard.Key) -> None:
        if key != self.hotkey or not self.recorder.is_recording:
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
                copy_to_clipboard(text)
                if self.config.auto_type:
                    type_text(text)
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
        hotkey_name = self.hotkey.name if hasattr(self.hotkey, "name") else str(self.hotkey)
        print(f"Ready! Hold [{hotkey_name}] to record.")
        print("Press Ctrl+C to quit.")

        with keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        ) as listener:
            listener.join()
