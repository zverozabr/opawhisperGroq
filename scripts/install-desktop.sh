#!/bin/bash
# Install desktop entry and icon for SoupaWhisper

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Install desktop entry
echo "Installing desktop entry..."
cp "$PROJECT_DIR/data/soupawhisper.desktop" ~/.local/share/applications/

# Install icon
echo "Installing icon..."
mkdir -p ~/.local/share/icons/hicolor/48x48/apps
cp "$PROJECT_DIR/data/icons/soupawhisper.png" ~/.local/share/icons/hicolor/48x48/apps/

# Update icon cache
echo "Updating icon cache..."
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true

# Update desktop database
echo "Updating desktop database..."
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo "Done! SoupaWhisper is now available in your application menu."
