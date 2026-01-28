"""Centralized constants for SoupaWhisper.

This module contains all shared constants to avoid duplication (DRY principle).
"""

# Default transcription model
DEFAULT_MODEL = "whisper-large-v3"

# Default active provider
DEFAULT_PROVIDER = "groq"

# Groq API URL for transcription
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
