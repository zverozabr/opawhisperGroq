"""Tests for macOS permission helpers."""

import sys
from unittest.mock import patch

import pytest


class TestDarwinPermissionHelpers:
    """Tests for darwin.py permission functions."""

    def test_get_permission_target_returns_string(self):
        """get_permission_target returns a non-empty string."""
        if sys.platform != "darwin":
            pytest.skip("macOS only")

        from soupawhisper.backend.darwin import get_permission_target

        path = get_permission_target()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_permission_target_non_darwin(self):
        """get_permission_target returns 'Python' on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            from soupawhisper.backend import darwin

            result = darwin.get_permission_target()
            assert result == "Python"

    def test_get_permission_target_always_returns_python(self):
        """get_permission_target always returns Python path (not .app)."""
        if sys.platform != "darwin":
            pytest.skip("macOS only")

        import os
        from soupawhisper.backend.darwin import get_permission_target

        # Even when launched from app bundle, should return Python path
        # because macOS grants permissions to executables, not unsigned .app bundles
        with patch.dict(os.environ, {"__CFBundleIdentifier": "com.soupawhisper.app"}):
            path = get_permission_target()
            # Should NOT end with .app, should be Python path
            assert not path.endswith(".app")
            assert "python" in path.lower() or "Python" in path

    def test_check_accessibility_returns_bool(self):
        """check_accessibility returns boolean."""
        if sys.platform != "darwin":
            pytest.skip("macOS only")

        from soupawhisper.backend.darwin import check_accessibility

        result = check_accessibility(prompt=False)
        assert isinstance(result, bool)

    def test_check_accessibility_non_darwin(self):
        """check_accessibility returns True on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            from soupawhisper.backend import darwin

            result = darwin.check_accessibility()
            assert result is True

    def test_needs_input_monitoring_returns_bool(self):
        """needs_input_monitoring returns boolean."""
        from soupawhisper.backend.darwin import needs_input_monitoring

        result = needs_input_monitoring()
        assert isinstance(result, bool)

    def test_needs_input_monitoring_non_darwin(self):
        """needs_input_monitoring returns False on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            from soupawhisper.backend import darwin

            result = darwin.needs_input_monitoring()
            assert result is False

    def test_open_accessibility_settings_callable(self):
        """open_accessibility_settings is callable."""
        from soupawhisper.backend.darwin import open_accessibility_settings

        assert callable(open_accessibility_settings)

    def test_open_input_monitoring_settings_callable(self):
        """open_input_monitoring_settings is callable."""
        from soupawhisper.backend.darwin import open_input_monitoring_settings

        assert callable(open_input_monitoring_settings)

    def test_open_accessibility_settings_non_darwin(self):
        """open_accessibility_settings does nothing on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            with patch("subprocess.Popen") as mock_popen:
                from soupawhisper.backend import darwin

                darwin.open_accessibility_settings()
                mock_popen.assert_not_called()

    def test_open_input_monitoring_settings_non_darwin(self):
        """open_input_monitoring_settings does nothing on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            with patch("subprocess.Popen") as mock_popen:
                from soupawhisper.backend import darwin

                darwin.open_input_monitoring_settings()
                mock_popen.assert_not_called()


class TestKeyboardPermissions:
    """Tests for check_keyboard_permissions function."""

    def test_check_keyboard_permissions_returns_bool(self):
        """check_keyboard_permissions returns boolean."""
        from soupawhisper.backend.darwin import check_keyboard_permissions

        result = check_keyboard_permissions()
        assert isinstance(result, bool)

    def test_check_keyboard_permissions_non_darwin(self):
        """check_keyboard_permissions returns True on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            from soupawhisper.backend import darwin

            result = darwin.check_keyboard_permissions()
            assert result is True


class TestMacOSPermissionCheck:
    """Tests for macOS permission checking with mocks."""

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
    def test_open_accessibility_settings_calls_open(self):
        """open_accessibility_settings calls 'open' command on macOS."""
        with patch("subprocess.Popen") as mock_popen:
            from soupawhisper.backend.darwin import open_accessibility_settings

            open_accessibility_settings()

            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args[0] == "open"
            assert "Privacy_Accessibility" in args[1]

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
    def test_open_input_monitoring_settings_calls_open(self):
        """open_input_monitoring_settings calls 'open' command on macOS."""
        with patch("subprocess.Popen") as mock_popen:
            from soupawhisper.backend.darwin import open_input_monitoring_settings

            open_input_monitoring_settings()

            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args[0] == "open"
            assert "Privacy_ListenEvent" in args[1]


class TestPermissionStatus:
    """Tests for PermissionStatus dataclass."""

    def test_all_granted_true(self):
        """all_granted is True when both permissions granted."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=True, accessibility=True)
        assert status.all_granted is True

    def test_all_granted_false_accessibility(self):
        """all_granted is False when accessibility missing."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=True, accessibility=False)
        assert status.all_granted is False

    def test_all_granted_false_input(self):
        """all_granted is False when input_monitoring missing."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=False, accessibility=True)
        assert status.all_granted is False

    def test_all_granted_false_both(self):
        """all_granted is False when both missing."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=False, accessibility=False)
        assert status.all_granted is False

    def test_missing_none(self):
        """missing is empty when all granted."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=True, accessibility=True)
        assert status.missing == []

    def test_missing_accessibility(self):
        """missing contains 'Accessibility' when not granted."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=True, accessibility=False)
        assert status.missing == ["Accessibility"]

    def test_missing_input_monitoring(self):
        """missing contains 'Input Monitoring' when not granted."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=False, accessibility=True)
        assert status.missing == ["Input Monitoring"]

    def test_missing_both(self):
        """missing contains both when neither granted."""
        from soupawhisper.backend.darwin import PermissionStatus

        status = PermissionStatus(input_monitoring=False, accessibility=False)
        assert "Input Monitoring" in status.missing
        assert "Accessibility" in status.missing
        assert len(status.missing) == 2


class TestPermissionsHelper:
    """Tests for PermissionsHelper class."""

    def test_check_returns_permission_status(self):
        """check() returns PermissionStatus instance."""
        from soupawhisper.backend.darwin import PermissionsHelper, PermissionStatus

        status = PermissionsHelper.check()
        assert isinstance(status, PermissionStatus)

    def test_check_non_darwin_returns_all_granted(self):
        """check() returns all granted on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            from soupawhisper.backend import darwin

            status = darwin.PermissionsHelper.check()
            assert status.all_granted is True

    def test_get_python_path_returns_string(self):
        """get_python_path() returns non-empty string."""
        from soupawhisper.backend.darwin import PermissionsHelper

        path = PermissionsHelper.get_python_path()
        assert isinstance(path, str)
        assert len(path) > 0

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
    def test_open_accessibility_with_finder(self):
        """open_accessibility_with_finder opens Finder and Settings."""
        with patch("subprocess.Popen") as mock_popen:
            with patch("soupawhisper.backend.darwin._copy") as mock_copy:
                from soupawhisper.backend.darwin import PermissionsHelper

                PermissionsHelper.open_accessibility_with_finder()

                # Should call Popen twice (Finder + Settings)
                assert mock_popen.call_count == 2
                # Should copy path to clipboard
                mock_copy.assert_called_once()

    def test_open_accessibility_with_finder_non_darwin(self):
        """open_accessibility_with_finder does nothing on non-macOS."""
        with patch.object(sys, "platform", "linux"):
            with patch("subprocess.Popen") as mock_popen:
                from soupawhisper.backend import darwin

                darwin.PermissionsHelper.open_accessibility_with_finder()
                mock_popen.assert_not_called()

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
    def test_log_status_returns_status(self):
        """log_status() returns PermissionStatus."""
        from soupawhisper.backend.darwin import PermissionsHelper, PermissionStatus

        status = PermissionsHelper.log_status()
        assert isinstance(status, PermissionStatus)
