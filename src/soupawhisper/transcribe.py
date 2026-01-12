"""Speech-to-text transcription via Groq API."""

from dataclasses import dataclass
from typing import Any

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class TranscriptionError(Exception):
    """Raised when transcription fails."""


@dataclass
class TranscriptionResult:
    """Result from transcription API."""

    text: str
    raw_response: dict[str, Any]


def transcribe(audio_path: str, api_key: str, model: str, language: str) -> TranscriptionResult:
    """
    Transcribe audio file using Groq Whisper API.

    Args:
        audio_path: Path to audio file (WAV format)
        api_key: Groq API key
        model: Whisper model name
        language: Language code (e.g., "ru", "en") or "auto" for auto-detection

    Returns:
        TranscriptionResult with text and raw API response

    Raises:
        TranscriptionError: If API call fails
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    data = {"model": model}
    if language != "auto":
        data["language"] = language

    with open(audio_path, "rb") as f:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            files={"file": ("audio.wav", f, "audio/wav")},
            data=data,
            timeout=30,
        )

    if not response.ok:
        raise TranscriptionError(f"API error {response.status_code}: {response.text}")

    response_json = response.json()
    return TranscriptionResult(
        text=response_json.get("text", "").strip(),
        raw_response=response_json,
    )
