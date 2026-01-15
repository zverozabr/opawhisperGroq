#!/bin/bash
# Install SoupaWhisper.app for macOS Spotlight
# KISS: One script, one task - create .app bundle
# DRY: Variables at the top

set -e

APP_NAME="SoupaWhisper"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_DIR="$HOME/Applications/${APP_NAME}.app"
ICON_SRC="$PROJECT_DIR/src/soupawhisper/gui/assets/microphone.png"

echo "Installing ${APP_NAME}.app..."

# Create app bundle structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.soupawhisper.app</string>
    <key>CFBundleName</key>
    <string>SoupaWhisper</string>
    <key>CFBundleDisplayName</key>
    <string>SoupaWhisper</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launcher script
cat > "$APP_DIR/Contents/MacOS/launcher" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
exec uv run soupawhisper --gui
EOF
chmod +x "$APP_DIR/Contents/MacOS/launcher"

# Convert PNG to ICNS
if [ -f "$ICON_SRC" ]; then
    echo "Creating app icon..."
    ICONSET_DIR=$(mktemp -d)/AppIcon.iconset
    mkdir -p "$ICONSET_DIR"

    # Create icon sizes
    sips -z 512 512 "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512.png" 2>/dev/null || cp "$ICON_SRC" "$ICONSET_DIR/icon_512x512.png"
    sips -z 256 256 "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256.png" 2>/dev/null || true
    sips -z 128 128 "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128.png" 2>/dev/null || true
    sips -z 64 64 "$ICON_SRC" --out "$ICONSET_DIR/icon_64x64.png" 2>/dev/null || true
    sips -z 32 32 "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32.png" 2>/dev/null || true
    sips -z 16 16 "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16.png" 2>/dev/null || true

    # Convert to icns
    if iconutil -c icns "$ICONSET_DIR" -o "$APP_DIR/Contents/Resources/AppIcon.icns" 2>/dev/null; then
        echo "Icon created successfully."
    else
        echo "Warning: Could not create icns, using PNG fallback."
        cp "$ICON_SRC" "$APP_DIR/Contents/Resources/AppIcon.png"
    fi

    rm -rf "$(dirname "$ICONSET_DIR")"
else
    echo "Warning: Icon not found at $ICON_SRC"
fi

# Touch to update Spotlight index
touch "$APP_DIR"

echo ""
echo "Done! ${APP_NAME} is now available in Spotlight."
echo "Location: $APP_DIR"
echo ""
echo "Press Cmd+Space and type '${APP_NAME}' to launch."
