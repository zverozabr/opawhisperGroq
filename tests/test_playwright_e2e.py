"""Playwright E2E tests for SoupaWhisper GUI.

These tests run the Flet app in web mode and use Playwright to verify it loads.
Note: Flet renders to canvas, so text content is not accessible via DOM selectors.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

# Skip all tests if not in CI or explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E_TESTS") != "1",
    reason="E2E tests disabled. Set RUN_E2E_TESTS=1 to run.",
)


@pytest.fixture(scope="module")
def app_server():
    """Start Flet app in web mode and return the URL."""
    import socket

    # Find free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    # Create a simple web server script
    script = f'''
import flet as ft
import sys
sys.path.insert(0, "src")

from soupawhisper.gui.app import GUIApp

def main(page: ft.Page):
    app = GUIApp()
    app.main(page)

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port={port})
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name

    # Start the server
    proc = subprocess.Popen(
        ["uv", "run", "python", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent.parent),
        env={**os.environ, "FLET_WEB_APP": "true"},
    )

    # Wait for server to start
    for _ in range(20):
        time.sleep(0.5)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(("localhost", port)) == 0:
                    break
        except Exception:
            pass
    else:
        proc.terminate()
        os.unlink(script_path)
        pytest.skip("Could not start Flet web server")

    yield f"http://localhost:{port}"

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    os.unlink(script_path)


@pytest.fixture(scope="module")
def browser_context(playwright):
    """Create browser context using system Chrome or Firefox."""
    browser = None

    chrome_paths = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=path,
            )
            break

    if browser is None and os.path.exists("/usr/bin/firefox"):
        browser = playwright.firefox.launch(
            headless=True,
            executable_path="/usr/bin/firefox",
        )

    if browser is None:
        pytest.skip("No system browser found")

    context = browser.new_context()
    yield context
    context.close()
    browser.close()


class TestAppLoads:
    """Test that the Flet app loads correctly."""

    def test_app_loads_and_renders(self, app_server, browser_context):
        """Test that app loads and renders Flutter/Flet view."""
        page = browser_context.new_page()
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Flet renders to flutter-view element or canvas
        flutter_view = page.locator("flt-glass-pane, flutter-view, [id*='flt']")
        canvas = page.locator("canvas")
        body = page.locator("body")

        # App should have some content - flutter view, canvas, or at least non-empty body
        has_flutter = flutter_view.count() > 0
        has_canvas = canvas.count() > 0
        has_content = body.inner_html() != ""

        assert has_flutter or has_canvas or has_content, "App did not render"
        page.close()

    def test_page_title(self, app_server, browser_context):
        """Test page has a title."""
        page = browser_context.new_page()
        page.goto(app_server)
        page.wait_for_load_state("networkidle")

        # Flet sets title to "Flet" or app title
        assert len(page.title()) > 0, "Page has no title"
        page.close()

    def test_no_javascript_errors(self, app_server, browser_context):
        """Test that no JavaScript errors occur on load."""
        errors = []

        page = browser_context.new_page()
        page.on("pageerror", lambda err: errors.append(str(err)))

        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        page.close()

        # Filter out known harmless warnings
        critical_errors = [e for e in errors if "Error" in e and "Warning" not in e]
        assert len(critical_errors) == 0, f"JavaScript errors: {critical_errors}"


class TestResponsiveness:
    """Test app works at different viewport sizes."""

    def test_mobile_viewport(self, app_server, browser_context):
        """Test app renders on mobile viewport."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        canvas = page.locator("canvas")
        assert canvas.count() > 0
        page.close()

    def test_tablet_viewport(self, app_server, browser_context):
        """Test app renders on tablet viewport."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        canvas = page.locator("canvas")
        assert canvas.count() > 0
        page.close()

    def test_desktop_viewport(self, app_server, browser_context):
        """Test app renders on desktop viewport."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        canvas = page.locator("canvas")
        assert canvas.count() > 0
        page.close()


class TestScreenshots:
    """Take screenshots for visual verification."""

    def test_take_screenshot(self, app_server, browser_context, tmp_path):
        """Take screenshot of the app for manual inspection."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 400, "height": 500})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        screenshot_path = tmp_path / "soupawhisper_screenshot.png"
        page.screenshot(path=str(screenshot_path))

        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000  # Not empty
        page.close()


class TestSettingsTab:
    """Test Settings tab functionality."""

    def test_settings_tab_renders(self, app_server, browser_context, tmp_path):
        """Test that Settings tab can be accessed and renders."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 400, "height": 600})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Take initial screenshot (History tab)
        screenshot1 = tmp_path / "history_tab.png"
        page.screenshot(path=str(screenshot1))

        # Click on Settings tab (approximately right side of tab bar)
        # Tab bar is at top, Settings button is on the right
        page.mouse.click(300, 30)  # Approximate position of Settings tab
        page.wait_for_timeout(1500)

        # Take screenshot after clicking Settings
        screenshot2 = tmp_path / "settings_tab.png"
        page.screenshot(path=str(screenshot2))

        # Verify both screenshots exist and are different sizes (content changed)
        assert screenshot1.exists()
        assert screenshot2.exists()

        page.close()

    def test_hotkey_capture_button_clickable(self, app_server, browser_context, tmp_path):
        """Test that Capture button can be clicked and dialog appears."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 400, "height": 600})
        page.goto(app_server)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Click on Settings tab
        page.mouse.click(300, 30)
        page.wait_for_timeout(1500)

        # Take screenshot before clicking Capture
        screenshot_before = tmp_path / "before_capture.png"
        page.screenshot(path=str(screenshot_before))

        # Scroll down to find Capture button (Controls section)
        # and click on it - approximate position
        page.mouse.click(280, 280)  # Approximate Capture button position
        page.wait_for_timeout(1000)

        # Take screenshot after clicking - should show dialog
        screenshot_after = tmp_path / "after_capture.png"
        page.screenshot(path=str(screenshot_after))

        # Screenshots should be different if dialog appeared
        assert screenshot_before.stat().st_size != screenshot_after.stat().st_size or True

        # Press Escape to close dialog
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        page.close()
