# SoupaWhisper - Claude Context

Voice dictation tool for Linux X11 using Groq Whisper API.

## Tech Stack

- Python 3.11+
- UV package manager
- pynput (keyboard listener)
- requests (HTTP client)
- ALSA arecord (audio capture)
- xclip (clipboard)
- xdotool (text typing)

## Architecture

```
__main__.py  →  App  →  AudioRecorder  →  transcribe()  →  output
     ↓           ↓
   lock      config
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main App class, hotkey handling, orchestration |
| `audio.py` | AudioRecorder - ALSA arecord wrapper |
| `transcribe.py` | Groq Whisper API client |
| `config.py` | Config dataclass, INI file parsing |
| `output.py` | copy_to_clipboard(), type_text(), notify() |
| `lock.py` | Single instance via PID file |

## Config Location

`~/.config/soupawhisper/config.ini`

## API

Groq Whisper API:
- Endpoint: `https://api.groq.com/openai/v1/audio/transcriptions`
- Model: `whisper-large-v3`
- Auth: Bearer token

## Run

```bash
cd ~/work/soupawhisper
uv run soupawhisper
```

## Desktop Entry

`~/.local/share/applications/soupawhisper.desktop`

## Lock File

`~/.cache/soupawhisper.lock` (contains PID)
