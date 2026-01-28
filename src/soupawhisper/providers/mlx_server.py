#!/usr/bin/env python3
"""MLX Model Server - Long-running process with model cached in memory.

This script runs as a separate process that:
1. Loads the MLX whisper model once at startup
2. Listens for transcription requests via stdin (JSON)
3. Returns results via stdout (JSON)
4. Keeps model in memory between requests for instant transcription

Protocol:
- Request (JSON): {"audio_path": "/path/to/audio.wav", "language": "auto", "model": "mlx-community/..."}
- Response (JSON): {"text": "transcribed text", "time_ms": 1234}
- Error (JSON): {"error": "error message"}

Usage:
    python -m soupawhisper.providers.mlx_server
"""

import json
import sys
import time
import logging

# Setup logging to stderr (stdout is for IPC)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [MLX-Server] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)


def main():
    """Main server loop."""
    log.info("MLX Model Server starting...")

    # Current model path (for cache invalidation)
    current_model_path = None

    # Pre-import mlx_whisper to warm up
    try:
        import mlx_whisper
        log.info("mlx_whisper imported successfully")
    except ImportError as e:
        error = {"error": f"Failed to import mlx_whisper: {e}"}
        print(json.dumps(error), flush=True)
        sys.exit(1)

    log.info("Ready. Waiting for requests on stdin...")

    # Send ready signal
    print(json.dumps({"status": "ready"}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            error = {"error": f"Invalid JSON: {e}"}
            print(json.dumps(error), flush=True)
            continue

        # Handle shutdown command
        if request.get("command") == "shutdown":
            log.info("Shutdown requested")
            print(json.dumps({"status": "shutdown"}), flush=True)
            break

        # Handle transcription request
        audio_path = request.get("audio_path")
        language = request.get("language", "auto")
        model_path = request.get("model", "mlx-community/whisper-large-v3-turbo")

        if not audio_path:
            error = {"error": "Missing audio_path"}
            print(json.dumps(error), flush=True)
            continue

        log.info(f"Transcribing: {audio_path}")
        start_time = time.perf_counter()

        try:
            # Check if model changed
            if model_path != current_model_path:
                log.info(f"Loading model: {model_path}")
                current_model_path = model_path

            # Transcribe - ModelHolder inside mlx_whisper caches the model
            result = mlx_whisper.transcribe(
                audio_path,
                path_or_hf_repo=model_path,
                language=None if language == "auto" else language,
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            text = result.get("text", "").strip()

            log.info(f"Transcription complete in {elapsed_ms}ms: {text[:50]}...")

            response = {
                "text": text,
                "time_ms": elapsed_ms,
                "language": result.get("language", language),
            }
            print(json.dumps(response), flush=True)

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            log.error(f"Transcription failed after {elapsed_ms}ms: {e}")
            error = {"error": str(e), "time_ms": elapsed_ms}
            print(json.dumps(error), flush=True)

    log.info("Server stopped")


if __name__ == "__main__":
    main()
