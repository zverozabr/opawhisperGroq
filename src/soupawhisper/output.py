"""Output handling - notifications."""

import subprocess
import sys

# Fixed notification ID for replacement (works on most DEs)
_NOTIFICATION_ID = 999888777


def notify(title: str, message: str, icon: str = "dialog-information", timeout_ms: int = 2000) -> None:
    """Show desktop notification, replacing any previous one.

    Platform support:
    - macOS: osascript (AppleScript)
    - Linux: notify-send (freedesktop)
    - Windows: PowerShell toast notification
    """
    if sys.platform == "darwin":
        # macOS: Use osascript
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            check=False,
        )
    elif sys.platform == "win32":
        # Windows: PowerShell toast
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("{title}")) | Out-Null
        $xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode("{message}")) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SoupaWhisper").Show($toast)
        '''
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            check=False,
        )
    else:
        # Linux: notify-send
        subprocess.run(
            [
                "notify-send",
                "-a", "SoupaWhisper",
                "-i", icon,
                "-t", str(timeout_ms),
                "-r", str(_NOTIFICATION_ID),
                "-h", "string:x-canonical-private-synchronous:soupawhisper",
                title,
                message,
            ],
            capture_output=True,
            check=False,
        )
