# SoupaWhisper

Voice dictation tool for Linux (X11) using Groq Whisper API.

## Features

- Push-to-talk voice input (hold Right Ctrl)
- Fast cloud transcription via Groq API (whisper-large-v3)
- Auto-types text into active window
- Copies to clipboard
- Desktop notifications
- Single instance lock
- Supports 100+ languages

## Requirements

- Arch Linux / X11
- Python 3.11+
- System: `alsa-utils`, `xclip`, `xdotool`

## Installation

```bash
sudo pacman -S alsa-utils xclip xdotool

cd ~/work/soupawhisper
uv sync
```

## Configuration

`~/.config/soupawhisper/config.ini`:

```ini
[groq]
api_key = YOUR_GROQ_API_KEY
model = whisper-large-v3
language = ru

[hotkey]
key = ctrl_r

[behavior]
auto_type = true
notifications = true
```

Get API key: https://console.groq.com/

## Usage

```bash
uv run soupawhisper
```

- Hold **Right Ctrl** — record
- Release — transcribe & type

## Structure

```
src/soupawhisper/
├── __init__.py      # Version
├── __main__.py      # Entry point
├── app.py           # Main logic
├── audio.py         # ALSA recording
├── config.py        # INI config
├── lock.py          # Single instance
├── output.py        # Clipboard/xdotool
└── transcribe.py    # Groq API
```

## License

MIT
