"""E2E tests for transcription flow using real debug recordings."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Real transcription samples from debug recordings
TRANSCRIPTION_SAMPLES = [
    {
        "expected_text": "раз два три 4 5 вышел зайчик погулять",
        "response": {"text": " раз два три 4 5 вышел зайчик погулять"},
    },
]


class TestTranscriptionE2E:
    """End-to-end tests for transcription pipeline."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.api_key = "test_key"
        config.model = "whisper-large-v3"
        config.language = "auto"
        config.notifications = False
        config.auto_type = True
        config.auto_enter = False
        config.debug = False
        return config

    @pytest.fixture
    def mock_backend(self):
        """Create mock backend."""
        backend = MagicMock()
        backend.copy_to_clipboard = MagicMock()
        backend.type_text = MagicMock(return_value="xdotool")
        return backend

    @pytest.fixture
    def temp_audio(self):
        """Create temporary audio file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Write minimal WAV header (silent audio)
            f.write(b"RIFF")
            f.write((36).to_bytes(4, "little"))  # file size - 8
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write((16).to_bytes(4, "little"))  # chunk size
            f.write((1).to_bytes(2, "little"))   # PCM
            f.write((1).to_bytes(2, "little"))   # mono
            f.write((16000).to_bytes(4, "little"))  # sample rate
            f.write((32000).to_bytes(4, "little"))  # byte rate
            f.write((2).to_bytes(2, "little"))   # block align
            f.write((16).to_bytes(2, "little"))  # bits per sample
            f.write(b"data")
            f.write((0).to_bytes(4, "little"))   # data size
            path = Path(f.name)
        yield path
        path.unlink(missing_ok=True)

    @pytest.mark.parametrize("sample", TRANSCRIPTION_SAMPLES)
    def test_transcription_flow(self, sample, mock_config, mock_backend, temp_audio):
        """Test full transcription flow with real sample data."""
        from soupawhisper.transcribe import TranscriptionResult
        from soupawhisper.transcription_handler import TranscriptionContext, TranscriptionHandler

        expected_text = sample["expected_text"]
        mock_response = sample["response"]

        # Mock transcribe to return real response
        with patch("soupawhisper.transcription_handler.transcribe") as mock_transcribe:
            mock_transcribe.return_value = TranscriptionResult(
                text=mock_response["text"].strip(),
                raw_response=mock_response,
            )

            handler = TranscriptionHandler(mock_config)
            completed = []

            ctx = TranscriptionContext(
                audio_path=temp_audio,
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
                on_complete=lambda text, lang: completed.append((text, lang)),
            )

            handler.handle(ctx)

            # Verify transcription result
            assert len(completed) == 1
            text, lang = completed[0]
            assert text == expected_text

            # Verify clipboard was updated
            mock_backend.copy_to_clipboard.assert_called_with(expected_text)

            # Verify text was typed
            mock_backend.type_text.assert_called_with(expected_text)

    def test_transcription_with_debug_storage(self, mock_config, mock_backend, temp_audio):
        """Test transcription saves debug data."""
        from soupawhisper.storage import DebugStorage
        from soupawhisper.transcribe import TranscriptionResult
        from soupawhisper.transcription_handler import TranscriptionContext, TranscriptionHandler

        mock_config.debug = True

        with tempfile.TemporaryDirectory() as tmpdir:
            debug_storage = DebugStorage(debug_dir=Path(tmpdir))

            with patch("soupawhisper.transcription_handler.transcribe") as mock_transcribe:
                mock_transcribe.return_value = TranscriptionResult(
                    text="тестовый текст",
                    raw_response={"text": " тестовый текст"},
                )

                handler = TranscriptionHandler(mock_config)

                ctx = TranscriptionContext(
                    audio_path=temp_audio,
                    config=mock_config,
                    backend=mock_backend,
                    debug_storage=debug_storage,
                    on_complete=lambda text, lang: None,
                )

                handler.handle(ctx)

            # Verify debug files were created
            debug_dirs = list(Path(tmpdir).glob("*"))
            assert len(debug_dirs) == 1

            debug_dir = debug_dirs[0]
            assert (debug_dir / "text.txt").exists()
            assert (debug_dir / "response.json").exists()
            assert (debug_dir / "clipboard.txt").exists()
            assert (debug_dir / "typed.txt").exists()

            # Verify content
            assert (debug_dir / "text.txt").read_text().strip() == "тестовый текст"

    def test_empty_transcription_not_typed(self, mock_config, mock_backend, temp_audio):
        """Test empty transcription is not typed."""
        from soupawhisper.transcribe import TranscriptionResult
        from soupawhisper.transcription_handler import TranscriptionContext, TranscriptionHandler

        with patch("soupawhisper.transcription_handler.transcribe") as mock_transcribe:
            mock_transcribe.return_value = TranscriptionResult(
                text="",
                raw_response={"text": ""},
            )

            handler = TranscriptionHandler(mock_config)

            ctx = TranscriptionContext(
                audio_path=temp_audio,
                config=mock_config,
                backend=mock_backend,
                debug_storage=None,
                on_complete=lambda text, lang: None,
            )

            handler.handle(ctx)

            # Empty text should not trigger clipboard/type
            mock_backend.copy_to_clipboard.assert_not_called()
            mock_backend.type_text.assert_not_called()


class TestClipboardPasteFlow:
    """Test clipboard + paste flow (X11/Wayland)."""

    def test_x11_uses_xdotool_type(self):
        """Test X11 backend uses xdotool type for text input."""
        import sys
        from unittest.mock import MagicMock, patch

        mock_keyboard = MagicMock()
        with patch.dict(sys.modules, {'pynput': MagicMock(), 'pynput.keyboard': mock_keyboard}):
            with patch("subprocess.run") as mock_run:
                from soupawhisper.backend.x11 import X11Backend

                backend = X11Backend()
                method = backend.type_text("кириллица")

                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert "type" in call_args
                assert "кириллица" in call_args
                assert method == "xdotool"

    def test_wayland_fallback_to_clipboard(self):
        """Test Wayland backend falls back to clipboard when typing unavailable."""
        with patch("soupawhisper.backend.wayland._has_command", return_value=False):
            from soupawhisper.backend.wayland import WaylandBackend

            backend = WaylandBackend()
            method = backend.type_text("тест")

            assert method == "clipboard"
