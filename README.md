# SoupaWhisper

Voice dictation tool for Linux/macOS using Groq Whisper API.

## Features

- Push-to-talk voice input (hold Right Ctrl)
- Fast cloud transcription via Groq API (whisper-large-v3)
- Auto-types text into active window
- Copies to clipboard
- Desktop notifications
- Single instance lock
- Supports 100+ languages (auto-detect or specify)
- Multi-platform: X11, Wayland, macOS

## Requirements

### Linux (X11)
```bash
sudo pacman -S alsa-utils xclip xdotool  # Arch
sudo apt install alsa-utils xclip xdotool  # Debian/Ubuntu
```

### Linux (Wayland)
```bash
sudo pacman -S alsa-utils wl-clipboard wtype  # Arch
sudo apt install alsa-utils wl-clipboard wtype  # Debian/Ubuntu

# For hotkey support (add user to input group)
sudo usermod -aG input $USER
# Re-login required
```

### macOS
```bash
brew install sox
```

## Installation

```bash
cd ~/work/soupawhisper
uv sync
```

## Configuration

`~/.config/soupawhisper/config.ini`:

```ini
[groq]
api_key = YOUR_GROQ_API_KEY
model = whisper-large-v3
language = auto  # or "ru", "en", etc.

[hotkey]
key = ctrl_r

[behavior]
auto_type = true
auto_enter = false
typing_delay = 12  # ms between keystrokes (0 = fastest)
notifications = true
backend = auto  # auto, x11, wayland, darwin
```

Get API key: https://console.groq.com/

## Usage

```bash
uv run soupawhisper
```

- Hold **Right Ctrl** — record
- Release — transcribe & type

## Platform Notes

| Platform | Clipboard | Typing | Hotkeys |
|----------|-----------|--------|---------|
| X11 | xclip | xdotool | pynput |
| Wayland | wl-copy | wtype/ydotool | evdev |
| macOS | pbcopy | pynput | pynput |

**KDE Wayland:** Virtual keyboard blocked by security. Text copies to clipboard only — paste with Ctrl+V.

## License

MIT
