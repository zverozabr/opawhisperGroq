# SoupaWhisper

Voice dictation tool using Groq Whisper API.

**Multi-platform:** Linux (X11/Wayland), macOS, Windows

## Features

- Push-to-talk voice input (hold Right Ctrl)
- Fast cloud transcription via Groq API (whisper-large-v3)
- Auto-types text into active window
- Copies to clipboard
- Desktop notifications
- **GUI mode** with history and settings
- **Debug mode** - save recordings for troubleshooting
- Single instance lock
- Supports 100+ languages (auto-detect or specify)

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
brew install ffmpeg
```

**Note:** Grant Accessibility permissions: System Settings → Privacy & Security → Accessibility

### Windows
```bash
# Install ffmpeg (required for audio recording)
choco install ffmpeg
# or download from https://ffmpeg.org/download.html
```

## Installation

```bash
git clone https://github.com/yourusername/soupawhisper
cd soupawhisper
uv sync
```

### Desktop Integration

**Linux** (Application Menu):
```bash
./scripts/install-desktop.sh
```

**macOS** (Spotlight):
```bash
./scripts/install-macos.sh
```

**Windows** (Start Menu):
```powershell
.\scripts\install-windows.ps1
```

## Configuration

`~/.config/soupawhisper/config.ini`:

```ini
[groq]
api_key = YOUR_GROQ_API_KEY
model = whisper-large-v3
language = auto  # or "ru", "en", "de", "fr", etc.

[hotkey]
key = ctrl_r  # ctrl_r, ctrl_l, alt_r, f9-f12

[behavior]
auto_type = true
auto_enter = false
typing_delay = 12  # ms between keystrokes (0 = fastest)
notifications = true
backend = auto  # auto, x11, wayland, darwin, windows
debug = false  # save recordings to ~/.cache/soupawhisper/debug/

[history]
enabled = true
days = 7  # keep history for N days
```

Get API key: https://console.groq.com/

## Usage

### CLI Mode
```bash
uv run soupawhisper
```

### GUI Mode
```bash
uv run soupawhisper --gui
```

**Controls:**
- Hold **Right Ctrl** — record
- Release — transcribe & type

## Platform Support

| Platform | Audio | Clipboard | Typing | Hotkeys |
|----------|-------|-----------|--------|---------|
| X11 | arecord | xclip | xdotool | pynput |
| Wayland | arecord | wl-copy | wtype/ydotool | evdev |
| macOS | ffmpeg | pbcopy | pynput | pynput |
| Windows | ffmpeg | PowerShell | pynput | pynput |

**KDE Wayland:** Virtual keyboard blocked by security. Text copies to clipboard only — paste with Ctrl+V.

## Debug Mode

Enable debug mode to save the last 3 recordings:

```ini
[behavior]
debug = true
```

Files saved to `~/.cache/soupawhisper/debug/`:
- `audio.wav` - recorded audio
- `text.txt` - transcribed text
- `response.json` - full API response

## Development

```bash
# Run tests
uv run pytest -v

# Run linting
uv tool run ruff check src/ tests/

# Run with debug logging
uv run soupawhisper --debug
```

## License

MIT
