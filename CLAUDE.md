# SoupaWhisper - Claude Context

Voice dictation tool using Groq Whisper API.

**Multi-platform:** Linux (X11/Wayland), macOS, Windows

## Claude Instructions

- **Всегда использовать Exa (`mcp__exa__web_search_exa`) для веб-поиска, не WebSearch**

## Tech Stack

- Python 3.11+
- UV package manager
- Flet (GUI framework)
- pynput (keyboard listener - X11/macOS/Windows)
- evdev (keyboard listener - Wayland only)
- requests (HTTP client)

## Architecture

```
__main__.py  →  App  →  AudioRecorder  →  TranscriptionHandler  →  backend
     ↓           ↓            ↓                    ↓                  ↓
   lock      config      platform            transcribe()     X11/Wayland/
                        (arecord/                              Darwin/Windows
                         sox/ffmpeg)

GUI Mode:
__main__.py --gui  →  GUIApp  →  HistoryTab / SettingsTab
                         ↓              ↓
                       TrayIcon    HistoryStorage
```

## Directory Structure

```
src/soupawhisper/
├── __main__.py           # Entry point, CLI args
├── app.py                # Core App class, orchestration
├── audio.py              # AudioRecorder - platform audio capture
├── clipboard.py          # Cross-platform clipboard (DRY)
├── transcribe.py         # Groq Whisper API client
├── transcription_handler.py  # Handles transcription workflow (SRP)
├── config.py             # Config dataclass, validation, INI parsing
├── output.py             # notify() - desktop notifications
├── lock.py               # Single instance via PID file
├── logging.py            # Centralized logging
│
├── backend/              # Display backend abstraction
│   ├── __init__.py       # create_backend(), detect_backend_type()
│   ├── base.py           # DisplayBackend Protocol
│   ├── keys.py           # Shared key mapping (DRY)
│   ├── pynput_listener.py  # Shared pynput listener (DRY)
│   ├── x11.py            # X11: xclip, xdotool
│   ├── wayland.py        # Wayland: wl-copy, wtype/ydotool, evdev
│   ├── darwin.py         # macOS: pbcopy, pynput
│   └── windows.py        # Windows: PowerShell, pynput
│
├── storage/              # Data persistence
│   ├── __init__.py
│   ├── history.py        # HistoryStorage - transcription history
│   └── debug.py          # DebugStorage - save recordings for debug
│
└── gui/                  # Flet GUI
    ├── __init__.py
    ├── app.py            # GUIApp controller
    ├── components.py     # EditableField, SettingsSection
    ├── history_tab.py    # History display
    ├── settings_tab.py   # Settings form
    ├── tray.py           # System tray (pystray)
    └── assets/           # Icons
```

## Platform Support

| Platform | Audio | Clipboard | Typing | Hotkeys |
|----------|-------|-----------|--------|---------|
| X11 | arecord | xclip | xdotool | pynput |
| Wayland | arecord | wl-copy | wtype/ydotool | evdev |
| macOS | sox/rec | pbcopy | pynput | pynput |
| Windows | ffmpeg | PowerShell | pynput | pynput |

**Note:** KDE Wayland blocks virtual input — uses clipboard + manual paste

## Config

Location: `~/.config/soupawhisper/config.ini`

### Validation Constants (config.py)
```python
VALID_LANGUAGES = {"auto", "ru", "en", "de", "fr", "es", "zh", "ja", "ko", ...}
VALID_HOTKEYS = {"ctrl_r", "ctrl_l", "alt_r", "f12", "f11", "f10", "f9"}
VALID_BACKENDS = {"auto", "x11", "wayland", "darwin", "windows"}
```

## API

Groq Whisper API:
- Endpoint: `https://api.groq.com/openai/v1/audio/transcriptions`
- Model: `whisper-large-v3`
- Auth: Bearer token

## Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `App` | app.py | Orchestrates hotkey → record → transcribe |
| `TranscriptionHandler` | transcription_handler.py | Handles API call, clipboard, typing, debug |
| `AudioRecorder` | audio.py | Platform-specific audio capture |
| `PynputHotkeyListener` | backend/pynput_listener.py | Shared hotkey listener |
| `GUIApp` | gui/app.py | Flet GUI controller |
| `HistoryStorage` | storage/history.py | Markdown-based history |
| `DebugStorage` | storage/debug.py | Save recordings for debugging |

## Run

```bash
# CLI mode
uv run soupawhisper

# GUI mode
uv run soupawhisper --gui

# With debug logging
uv run soupawhisper --debug
```

## Testing

```bash
# All tests
uv run pytest -v

# Skip E2E tests
uv run pytest -v --ignore=tests/test_playwright_e2e.py --ignore=tests/test_gui_e2e.py

# Linting
uv tool run ruff check src/ tests/
```

## CI/CD

GitHub Actions: `.github/workflows/test.yml`
- Tests on: ubuntu-latest, windows-latest, macos-latest
- Lint check with ruff

## Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, build config |
| `uv.lock` | Locked dependencies |
| `docker/` | Docker setup for testing |
| `scripts/diagnose.py` | Debug tool for audio/API |
| `scripts/install-desktop.sh` | Install .desktop entry |
| `data/soupawhisper.desktop` | Desktop entry template |
