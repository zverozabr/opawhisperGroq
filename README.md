# SoupaWhisper

Voice dictation tool using Groq Whisper API.

**Multi-platform:** Linux (X11/Wayland), macOS, Windows

## Features

- Push-to-talk voice input (configurable hotkey)
- Fast cloud transcription via Groq API (whisper-large-v3)
- **Local transcription** — MLX (macOS Apple Silicon) and faster-whisper (cross-platform)
- Auto-types text into active window
- Copies to clipboard
- **TUI mode** — terminal interface with history and settings
- **Waveform visualization** — real-time audio level display during recording
- **Local model management** — download/delete models from UI
- **Platform-aware UI** — Command/Option on macOS, Ctrl/Alt on Linux/Windows
- Smart audio device selection with auto-reconnect
- Debug mode — save recordings for troubleshooting
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
# Required
sudo pacman -S alsa-utils wl-clipboard  # Arch
sudo apt install alsa-utils wl-clipboard  # Debian/Ubuntu

# Optional - for auto-typing (choose one):
yay -S wtype                    # Arch (AUR) - recommended, best Unicode support
sudo pacman -S ydotool          # Arch - alternative, needs ydotoold service

# For hotkey support (required - add user to input group)
sudo usermod -aG input $USER
# Re-login required after this!
```

**Note:** If no typing tool is installed, text is copied to clipboard only — paste with Ctrl+V.

**KDE Wayland:** Virtual keyboard is blocked by security policy. Use clipboard mode.

### macOS
```bash
brew install ffmpeg
```

**Permissions required:**
1. **Accessibility** — System Settings → Privacy & Security → Accessibility
2. **Input Monitoring** — System Settings → Privacy & Security → Input Monitoring

Add the application (or Cursor.app if running from IDE) to both lists.

### Windows
```bash
# Install ffmpeg (required for audio recording)
choco install ffmpeg
# or download from https://ffmpeg.org/download.html
```

## Installation

```bash
git clone https://github.com/zverozabr/opawhisperGroq
cd soupwhisper
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
key = super_r  # Right Command on macOS, Right Super on Linux

[audio]
device = default  # or specific device ID

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

### TUI Mode (default)
```bash
uv run soupawhisper
```

Terminal interface with tabs for History and Settings.

**Terminal Requirements:**
- Use a full-featured terminal: Terminal.app, iTerm2, Alacritty, Kitty
- IDE integrated terminals (Cursor, VS Code) may not render correctly
- Requires TERM with escape sequence support (xterm-256color recommended)

**Features:**
- Real-time waveform visualization during recording
- History browser with vim-style navigation
- Settings editor with live updates
- Local model management (download/delete)

**Keybindings:**
- `q` — Quit
- `h` — History tab
- `s` — Settings tab
- `c` — Copy selected transcription
- `j/k` — Navigate history (vim-style)
- `g/G` — Jump to top/bottom
- `Tab` / `Shift+Tab` — Navigate fields

### Headless Mode (CLI only)
```bash
uv run soupawhisper --headless
```

No UI, only hotkey listening.

**Recording Controls:**
- Hold **Right Command** (macOS) / **Right Super** (Linux) — record
- Release — transcribe & type
- Hotkey configurable in Settings

## Platform Support

| Platform | Audio | Clipboard | Typing | Hotkeys |
|----------|-------|-----------|--------|---------|
| X11 | arecord | xclip | xdotool | pynput |
| Wayland | arecord | wl-copy | wtype/ydotool | evdev |
| macOS | ffmpeg | pbcopy | pynput | pynput |
| Windows | ffmpeg | PowerShell | pynput | pynput |

**KDE Wayland:** Virtual keyboard blocked by security. Text copies to clipboard only — paste with Ctrl+V.

## macOS Permissions

If text is not being typed, check permissions:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Click **+** and add the app running SoupaWhisper:
   - If running from terminal: add your terminal app or Python
   - If running from Cursor: add `/Applications/Cursor.app`
3. Repeat for **Input Monitoring**

The GUI shows permission status and has a "Fix" button to help configure.

## Troubleshooting

### Arch Linux / Wayland

**"No keyboard devices found"**
```bash
# Add user to input group
sudo usermod -aG input $USER
# Re-login or reboot
```

**Hotkey not working**
- Check you're in `input` group: `groups | grep input`
- Check keyboard devices exist: `ls /dev/input/event*`
- Try running with `sudo` to test permissions

**Text not typing (Wayland)**
- Install `wtype` (AUR) or `ydotool`
- For ydotool, start the daemon: `sudo systemctl enable --now ydotool`
- KDE Wayland blocks virtual input — use clipboard mode (Ctrl+V)

**No sound / microphone not working**
```bash
# List available devices
arecord -l

# Test recording
arecord -d 3 test.wav && aplay test.wav
```

### macOS

**"Text not typing"**
1. System Settings → Privacy & Security → Accessibility
2. Add your terminal app (Terminal.app, iTerm2) or the running application
3. Also add to Input Monitoring

**"Permission denied" errors**
- Grant microphone access in System Settings → Privacy & Security → Microphone

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
# Run tests (480+ tests)
uv run pytest -v

# Run linting
uv tool run ruff check src/ tests/

# Run with debug logging
uv run soupawhisper --debug
```

### Architecture

The project follows SOLID, DRY, KISS principles:

- **TUI** — Textual-based terminal interface
- **WorkerController** — Manages background hotkey listener (SRP)
- **SettingsRegistry** — Declarative settings system (OCP)
- **CoreApp Protocol** — Abstraction for worker (DIP)

```
src/soupawhisper/
├── tui/                    # Terminal UI (Textual)
│   ├── app.py              # TUIApp - main controller
│   ├── settings_registry.py # Declarative settings (OCP)
│   ├── worker_controller.py # Worker lifecycle (SRP)
│   ├── screens/
│   │   ├── history.py      # History browser
│   │   └── settings.py     # Settings editor
│   └── widgets/
│       ├── status_bar.py   # Status display
│       ├── waveform.py     # Audio visualization
│       └── hotkey_input.py # Hotkey selector
├── worker.py               # Background worker manager
├── providers/              # Transcription providers
│   ├── models.py           # ModelManager for local models
│   ├── mlx.py              # MLX provider (macOS)
│   └── faster_whisper.py   # Faster-whisper provider
└── backend/                # Platform backends
```

## License

MIT
