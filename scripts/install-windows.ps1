# Install SoupaWhisper shortcut for Windows Start Menu
# KISS: Minimal code, using Windows COM objects
# DRY: Variables at the top

$ErrorActionPreference = "Stop"

$AppName = "SoupaWhisper"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$ShortcutPath = "$StartMenuPath\$AppName.lnk"
$IconPath = "$ProjectDir\src\soupawhisper\gui\assets\microphone.png"

Write-Host "Installing $AppName shortcut..."

# Find uv executable
$UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $UvPath) {
    $UvPath = "$env:USERPROFILE\.local\bin\uv.exe"
    if (-not (Test-Path $UvPath)) {
        $UvPath = "$env:LOCALAPPDATA\Programs\uv\uv.exe"
    }
}

if (-not (Test-Path $UvPath)) {
    Write-Error "uv not found. Please install uv first: https://docs.astral.sh/uv/"
    exit 1
}

# Create shortcut using WScript.Shell COM object
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $UvPath
$Shortcut.Arguments = "run soupawhisper --gui"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Voice dictation tool using Groq Whisper API"

# Set icon if available
if (Test-Path $IconPath) {
    # Note: Windows shortcuts need .ico files, PNG won't work directly
    # Using default icon from target executable
    Write-Host "Note: Using default icon (PNG to ICO conversion not available)"
}

$Shortcut.Save()

Write-Host ""
Write-Host "Done! $AppName is now available in Start Menu."
Write-Host "Location: $ShortcutPath"
Write-Host ""
Write-Host "Press Win key and type '$AppName' to launch."

# Optional: Create desktop shortcut
$CreateDesktop = Read-Host "Create desktop shortcut? (y/N)"
if ($CreateDesktop -eq "y" -or $CreateDesktop -eq "Y") {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\$AppName.lnk")
    $DesktopShortcut.TargetPath = $UvPath
    $DesktopShortcut.Arguments = "run soupawhisper --gui"
    $DesktopShortcut.WorkingDirectory = $ProjectDir
    $DesktopShortcut.Description = "Voice dictation tool using Groq Whisper API"
    $DesktopShortcut.Save()
    Write-Host "Desktop shortcut created!"
}
