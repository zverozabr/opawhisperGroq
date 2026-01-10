# SoupaWhisper - Claude Context

Voice dictation tool for Linux/macOS using Groq Whisper API.

## Claude Instructions

- **Всегда использовать Exa (`mcp__exa__web_search_exa`) для веб-поиска, не WebSearch**

## Tech Stack

- Python 3.11+
- UV package manager
- pynput (keyboard listener - X11/macOS)
- evdev (keyboard listener - Wayland)
- requests (HTTP client)

### Platform-specific
| Platform | Audio | Clipboard | Typing |
|----------|-------|-----------|--------|
| X11 | arecord | xclip | xdotool |
| Wayland | arecord | wl-copy | ydotool (Ctrl+V) |
| macOS | sox/rec | pbcopy | pynput |

**Note:** KDE Wayland блокирует виртуальный ввод — используется clipboard + ручная вставка

## Architecture

```
__main__.py  →  App  →  AudioRecorder  →  transcribe()  →  backend
     ↓           ↓                                           ↓
   lock      config                              X11/Wayland/Darwin
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main App class, orchestration |
| `audio.py` | AudioRecorder - platform audio capture |
| `transcribe.py` | Groq Whisper API client |
| `config.py` | Config dataclass, INI file parsing |
| `output.py` | notify() - desktop notifications |
| `lock.py` | Single instance via PID file |
| `backend/` | Display backend abstraction |
| `backend/base.py` | DisplayBackend Protocol |
| `backend/x11.py` | X11: xclip, xdotool, pynput |
| `backend/wayland.py` | Wayland: wl-copy, ydotool, evdev |
| `backend/darwin.py` | macOS: pbcopy, pynput |

## Config Location

`~/.config/soupawhisper/config.ini`

### Key Options
- `language = auto` — auto-detect, or specify code (`ru`, `en`)
- `typing_delay = 12` — ms between keystrokes (0 = fastest)
- `backend = auto` — auto, x11, wayland, darwin

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
