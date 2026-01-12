"""End-to-end tests for hotkey selector using Playwright.

These tests launch the actual GUI and interact with the virtual keyboard dialog.
"""

import os
import subprocess
import sys
import time

import pytest

# Skip if not running E2E tests
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E_TESTS") != "1",
    reason="E2E tests require GUI. Set RUN_E2E_TESTS=1 to run.",
)


@pytest.fixture(scope="module")
def app_process(tmp_path_factory):
    """Start the app in web mode for testing."""
    tmp_path = tmp_path_factory.mktemp("config")
    config_file = tmp_path / "config.ini"

    # Create minimal config
    config_file.write_text("""
[groq]
api_key = test_key_12345

[hotkey]
key = f9
""")

    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(tmp_path)
    env["SOUPAWHISPER_CONFIG"] = str(config_file)

    # Run app in web mode using test helper
    test_script = os.path.join(os.path.dirname(__file__), "run_web_app.py")
    proc = subprocess.Popen(
        [sys.executable, test_script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for web server to start
    time.sleep(4)

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestHotkeyDialogE2E:
    """E2E tests for hotkey selector dialog."""

    @pytest.fixture(autouse=True)
    def setup(self, app_process, page):
        """Navigate to the app and enable accessibility for DOM testing."""
        # Flet apps run on 127.0.0.1 with a specific port
        page.goto("http://127.0.0.1:8550")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)  # Wait for Flet to render

        # Enable Flutter accessibility to expose DOM elements
        page.evaluate("""() => {
            const placeholder = document.querySelector('flt-semantics-placeholder');
            if (placeholder) {
                placeholder.click();
            }
        }""")
        page.wait_for_timeout(1000)  # Wait for semantics tree to be built

    def test_settings_tab_visible(self, page):
        """Test that Settings tab is visible."""
        # Click Settings tab
        settings_tab = page.get_by_text("Settings")
        settings_tab.click()
        page.wait_for_timeout(1000)

        # Should see Hotkey section (use exact match for Flutter accessibility)
        hotkey_label = page.get_by_text("Hotkey", exact=True)
        hotkey_label.wait_for(timeout=5000)
        assert hotkey_label.is_visible()

    def _open_keyboard_dialog(self, page, clear: bool = True):
        """Helper to open the keyboard dialog."""
        page.get_by_text("Settings").click()
        page.wait_for_timeout(500)
        page.get_by_text("Change").click()
        # Wait for dialog to appear (Esc button is in the dialog)
        page.get_by_role("button", name="Esc").wait_for(timeout=5000)
        # Clear existing selection to avoid toggle issues
        if clear:
            page.get_by_role("button", name="Clear").click()
            page.wait_for_timeout(200)

    def test_change_button_opens_dialog(self, page):
        """Test that Change button opens keyboard dialog."""
        self._open_keyboard_dialog(page)
        # Dialog should have keyboard buttons
        assert page.get_by_role("button", name="F10").is_visible()

    def test_keyboard_has_function_keys(self, page):
        """Test that keyboard dialog shows function keys."""
        self._open_keyboard_dialog(page)

        # Check function keys are visible
        assert page.get_by_role("button", name="F9").is_visible()
        assert page.get_by_role("button", name="F10").is_visible()
        assert page.get_by_role("button", name="F11").is_visible()
        assert page.get_by_role("button", name="F12").is_visible()

    def test_keyboard_has_modifiers(self, page):
        """Test that keyboard dialog shows modifier keys."""
        self._open_keyboard_dialog(page)

        # Check modifier keys are visible (left and right variants)
        assert page.get_by_role("button", name="LCtrl").is_visible()
        assert page.get_by_role("button", name="RCtrl").is_visible()
        assert page.get_by_role("button", name="LAlt").is_visible()
        assert page.get_by_role("button", name="RAlt").is_visible()
        assert page.get_by_role("button", name="LSuper").is_visible()
        assert page.get_by_role("button", name="RSuper").is_visible()

    def test_select_function_key(self, page):
        """Test selecting a function key."""
        self._open_keyboard_dialog(page)

        # Click F10
        page.get_by_role("button", name="F10").click()

        # Selection should update
        page.wait_for_timeout(500)
        assert page.get_by_text("Selected: F10").is_visible()

    def test_select_combo_ctrl_g(self, page):
        """Test selecting LCtrl+G combo."""
        self._open_keyboard_dialog(page)

        # Click LCtrl (left ctrl)
        page.get_by_role("button", name="LCtrl").click()

        # Now G should be enabled - click it (use exact=True to avoid PgUp/PgDn)
        page.get_by_role("button", name="G", exact=True).click()

        # Selection should show combo (display shows "Left Ctrl + G")
        page.wait_for_timeout(500)
        assert page.get_by_text("Selected: Left Ctrl + G").is_visible()

    def test_cancel_closes_dialog(self, page):
        """Test that Cancel button closes dialog without saving."""
        self._open_keyboard_dialog(page)

        # Select F10
        page.get_by_role("button", name="F10").click()

        # Click Cancel
        page.get_by_role("button", name="Cancel").click()
        page.wait_for_timeout(500)

        # Dialog should close (Esc button not visible anymore)
        assert not page.get_by_role("button", name="Esc").is_visible()

    def test_save_updates_hotkey(self, page):
        """Test that Save button saves the new hotkey."""
        self._open_keyboard_dialog(page)

        # Select F11
        page.get_by_role("button", name="F11").click()
        page.wait_for_timeout(300)

        # Click Save
        page.get_by_role("button", name="Save").click()
        page.wait_for_timeout(500)

        # Dialog should close
        assert not page.get_by_role("button", name="Esc").is_visible()

    def test_letters_disabled_without_modifier(self, page):
        """Test that letter keys are disabled without modifier."""
        self._open_keyboard_dialog(page)

        # Letter G button should be disabled
        g_button = page.get_by_role("button", name="G", exact=True)
        assert g_button.is_disabled()

    def test_letters_enabled_with_modifier(self, page):
        """Test that letter keys become enabled when modifier selected."""
        self._open_keyboard_dialog(page)

        # Click Ctrl
        page.get_by_role("button", name="LCtrl").click()
        page.wait_for_timeout(500)  # Wait for UI to update

        # Letter G button should now be enabled
        g_button = page.get_by_role("button", name="G", exact=True)
        assert not g_button.is_disabled()

    def test_clear_button_clears_selection(self, page):
        """Test that Clear button clears the selection."""
        self._open_keyboard_dialog(page)

        # Select Ctrl+G
        page.get_by_role("button", name="LCtrl").click()
        page.get_by_role("button", name="G", exact=True).click()
        page.wait_for_timeout(300)

        # Click Clear
        page.get_by_role("button", name="Clear").click()
        page.wait_for_timeout(300)

        # Selection should be cleared
        assert page.get_by_text("Selected: Not set").is_visible()

    def test_toggle_modifier_in_combo(self, page):
        """Test clicking modifier again removes it from combo."""
        self._open_keyboard_dialog(page)

        # Select Ctrl+G
        page.get_by_role("button", name="LCtrl").click()
        page.get_by_role("button", name="G", exact=True).click()
        page.wait_for_timeout(300)

        # Click Ctrl again to remove it
        page.get_by_role("button", name="LCtrl").click()
        page.wait_for_timeout(300)

        # Should show "Not set" because G alone is invalid
        assert page.get_by_text("Selected: Not set").is_visible()

    def test_toggle_key_in_combo(self, page):
        """Test clicking key again removes it from combo."""
        self._open_keyboard_dialog(page)

        # Select Ctrl+G
        page.get_by_role("button", name="LCtrl").click()
        page.get_by_role("button", name="G", exact=True).click()
        page.wait_for_timeout(300)

        # Click G again to remove it
        page.get_by_role("button", name="G", exact=True).click()
        page.wait_for_timeout(300)

        # Should show just the modifier (now valid for push-to-talk style)
        assert page.get_by_text("Selected: Left Ctrl").is_visible()

    def test_keyboard_has_navigation_keys(self, page):
        """Test that keyboard dialog shows navigation keys."""
        self._open_keyboard_dialog(page)

        # Check navigation keys are visible (short labels due to button size)
        assert page.get_by_role("button", name="Hom").is_visible()
        assert page.get_by_role("button", name="End").is_visible()
        assert page.get_by_role("button", name="PgU").is_visible()
        assert page.get_by_role("button", name="PgD").is_visible()
        # Arrows
        assert page.get_by_role("button", name="↑").is_visible()
        assert page.get_by_role("button", name="↓").is_visible()
        assert page.get_by_role("button", name="←").is_visible()
        assert page.get_by_role("button", name="→").is_visible()

    def test_select_arrow_key(self, page):
        """Test selecting an arrow key."""
        self._open_keyboard_dialog(page)

        # Click up arrow
        page.get_by_role("button", name="↑").click()
        page.wait_for_timeout(300)

        # Selection should update
        assert page.get_by_text("Selected: ↑").is_visible()

    def test_select_right_alt(self, page):
        """Test selecting Right Alt modifier."""
        self._open_keyboard_dialog(page)

        # Click RAlt
        page.get_by_role("button", name="RAlt").click()

        # Now G should be enabled - click it
        page.get_by_role("button", name="G", exact=True).click()
        page.wait_for_timeout(300)

        # Selection should show combo
        assert page.get_by_text("Selected: Right Alt + G").is_visible()


class TestHotkeyMultipleCombosE2E:
    """E2E test for multiple hotkey combinations in a single session."""

    @pytest.fixture(autouse=True)
    def setup(self, app_process, browser):
        """Create fresh browser context for each test and navigate to app."""
        # Create a new browser context and page for each test
        # This ensures a fresh Flet session (old session disconnects, new one connects)
        context = browser.new_context()
        page = context.new_page()
        self.page = page

        page.goto("http://127.0.0.1:8550")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Enable Flutter accessibility
        page.evaluate("""() => {
            const placeholder = document.querySelector('flt-semantics-placeholder');
            if (placeholder) placeholder.click();
        }""")
        page.wait_for_timeout(1000)

        yield

        # Cleanup - close context to disconnect Flet session
        context.close()

    def _open_keyboard_dialog(self):
        """Open the keyboard dialog."""
        self.page.get_by_text("Settings").click()
        self.page.wait_for_timeout(500)
        self.page.get_by_text("Change").click()
        self.page.get_by_role("button", name="Esc").wait_for(timeout=5000)

    def _select_and_save(self, *keys):
        """Select keys and save. Clears existing selection first to avoid toggle issues."""
        self._open_keyboard_dialog()

        # Clear first to avoid toggling off existing selections
        self.page.get_by_role("button", name="Clear").click()
        self.page.wait_for_timeout(200)

        for key in keys:
            self.page.get_by_role("button", name=key, exact=True).click()
            self.page.wait_for_timeout(200)

        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(500)

    def _clear_and_save(self):
        """Clear selection and save."""
        self._open_keyboard_dialog()
        self.page.get_by_role("button", name="Clear").click()
        self.page.wait_for_timeout(200)
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(500)

    def test_multiple_combos_single_session(self):
        """Test multiple hotkey combinations in a single session with validation."""
        # === COMBO 1: Right Alt + G ===
        self._select_and_save("RAlt", "G")

        # Validate: re-open dialog and check selection
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Right Alt + G").is_visible()
        self.page.get_by_role("button", name="Cancel").click()
        self.page.wait_for_timeout(300)

        # === COMBO 2: Left Alt + Space ===
        self._select_and_save("LAlt", "Space")

        # Validate
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Left Alt + Space").is_visible()
        self.page.get_by_role("button", name="Cancel").click()
        self.page.wait_for_timeout(300)

        # === COMBO 3: Left Ctrl + A ===
        self._select_and_save("LCtrl", "A")

        # Validate
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Left Ctrl + A").is_visible()
        self.page.get_by_role("button", name="Cancel").click()
        self.page.wait_for_timeout(300)

        # === Test Clear then select new combo ===
        # Open dialog, clear, then select new combo and save
        self._open_keyboard_dialog()
        self.page.get_by_role("button", name="Clear").click()
        self.page.wait_for_timeout(200)
        # After clear, show "Not set" in the dialog
        assert self.page.get_by_text("Selected: Not set").is_visible()

        # Select a new combo and save
        self.page.get_by_role("button", name="RCtrl").click()
        self.page.get_by_role("button", name="B", exact=True).click()
        self.page.wait_for_timeout(200)
        assert self.page.get_by_text("Selected: Right Ctrl + B").is_visible()
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(500)

        # Validate
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Right Ctrl + B").is_visible()
        self.page.get_by_role("button", name="Cancel").click()
        self.page.wait_for_timeout(300)

        # === COMBO 4: Right Alt + Enter ===
        self._select_and_save("RAlt", "Enter")

        # Validate
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Right Alt + Enter").is_visible()
        self.page.get_by_role("button", name="Cancel").click()
        self.page.wait_for_timeout(300)

        # === COMBO 5: Left Alt + Tab ===
        self._select_and_save("LAlt", "Tab")

        # Validate
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Left Alt + Tab").is_visible()
        self.page.get_by_role("button", name="Cancel").click()

    def test_modifier_only_is_valid(self):
        """Test that modifier-only selections are valid for push-to-talk style."""
        # Clear and select only RAlt
        self._open_keyboard_dialog()
        self.page.get_by_role("button", name="Clear").click()
        self.page.wait_for_timeout(200)
        
        # Select just RAlt (no additional key)
        self.page.get_by_role("button", name="RAlt").click()
        self.page.wait_for_timeout(200)
        assert self.page.get_by_text("Selected: Right Alt").is_visible()
        
        # Save the modifier-only hotkey
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_timeout(500)

        # Validate it was saved - check the settings display shows "Right Alt"
        hotkey_text = self.page.get_by_text("Right Alt")
        assert hotkey_text.count() > 0
        
        # Re-open and verify it shows "Right Alt" (the saved value)
        self._open_keyboard_dialog()
        assert self.page.get_by_text("Selected: Right Alt").is_visible()
        self.page.get_by_role("button", name="Cancel").click()

    def test_all_modifier_combos_with_letter(self):
        """Test all left/right modifier combinations with letter keys."""
        combos = [
            (["LAlt", "X"], "Left Alt + X"),
            (["RAlt", "Y"], "Right Alt + Y"),
            (["LCtrl", "Z"], "Left Ctrl + Z"),
            (["RCtrl", "W"], "Right Ctrl + W"),
            (["LSuper", "D"], "Left Super + D"),
            (["RSuper", "E"], "Right Super + E"),
        ]

        for keys, expected_display in combos:
            # Select and save
            self._select_and_save(*keys)

            # Validate
            self._open_keyboard_dialog()
            assert self.page.get_by_text(f"Selected: {expected_display}").is_visible(), \
                f"Expected '{expected_display}' but not found"
            self.page.get_by_role("button", name="Cancel").click()
            self.page.wait_for_timeout(200)

    def test_special_key_combos(self):
        """Test combos with special keys like Space, Enter, Tab."""
        combos = [
            (["LCtrl", "Space"], "Left Ctrl + Space"),
            (["RAlt", "Enter"], "Right Alt + Enter"),
            (["LSuper", "Tab"], "Left Super + Tab"),
            (["RCtrl", "Bksp"], "Right Ctrl + Backspace"),
        ]

        for keys, expected_display in combos:
            self._select_and_save(*keys)

            self._open_keyboard_dialog()
            assert self.page.get_by_text(f"Selected: {expected_display}").is_visible(), \
                f"Expected '{expected_display}' but not found"
            self.page.get_by_role("button", name="Cancel").click()
            self.page.wait_for_timeout(200)
