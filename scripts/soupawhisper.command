#!/bin/bash
# SoupaWhisper - Voice Dictation Tool
# Run from Terminal for proper macOS permissions (Accessibility, Input Monitoring, Microphone)
#
# Double-click this file to launch SoupaWhisper GUI via Terminal.app
# Terminal.app must have permissions granted in System Settings > Privacy & Security

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

echo "=========================================="
echo "  SoupaWhisper - Voice Dictation"
echo "=========================================="
echo ""
echo "Project: $PROJECT_DIR"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv package manager not found."
    echo ""
    echo "Install uv with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Then restart Terminal and try again."
    exit 1
fi

echo "Starting GUI..."
echo ""

# Run SoupaWhisper GUI
exec uv run soupawhisper --gui
