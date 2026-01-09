"""Speech-to-text transcription via Groq API."""

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class TranscriptionError(Exception):
    """Raised when transcription fails."""


def transcribe(audio_path: str, api_key: str, model: str, language: str) -> str:
    """
    Transcribe audio file using Groq Whisper API.

    Args:
        audio_path: Path to audio file (WAV format)
        api_key: Groq API key
        model: Whisper model name
        language: Language code (e.g., "ru", "en")

    Returns:
        Transcribed text

    Raises:
        TranscriptionError: If API call fails
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(audio_path, "rb") as f:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            files={"file": ("audio.wav", f, "audio/wav")},
            data={"model": model, "language": language},
            timeout=30,
        )

    if not response.ok:
        raise TranscriptionError(f"API error {response.status_code}: {response.text}")

    return response.json().get("text", "").strip()
