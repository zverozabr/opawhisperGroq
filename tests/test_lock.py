"""Tests for single instance lock."""

import os
import signal
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestKillProcessTree:
    """Tests for _kill_process_tree function."""

    def test_kill_with_children(self):
        """Test killing process with child processes."""
        with patch("subprocess.run") as mock_run:
            with patch("os.kill") as mock_kill:
                # Mock pgrep: first call returns children, subsequent calls return empty
                mock_run.side_effect = [
                    MagicMock(stdout="1001\n1002\n"),  # Children of 1000
                    MagicMock(stdout=""),  # Children of 1001 (none)
                    MagicMock(stdout=""),  # Children of 1002 (none)
                ]

                from soupawhisper.lock import _kill_process_tree

                _kill_process_tree(1000)

                # Should call pgrep for main and each child
                assert mock_run.call_count == 3
                # Should kill all processes
                assert mock_kill.call_count == 3

    def test_kill_no_children(self):
        """Test killing process with no children."""
        with patch("subprocess.run") as mock_run:
            with patch("os.kill") as mock_kill:
                # Mock pgrep returning empty (no children)
                mock_run.return_value = MagicMock(stdout="")

                from soupawhisper.lock import _kill_process_tree

                _kill_process_tree(1000)

                mock_kill.assert_called_once_with(1000, signal.SIGTERM)

    def test_process_not_found(self):
        """Test handling when process doesn't exist."""
        with patch("subprocess.run") as mock_run:
            with patch("os.kill", side_effect=OSError("No such process")):
                mock_run.return_value = MagicMock(stdout="")

                from soupawhisper.lock import _kill_process_tree

                # Should not raise
                _kill_process_tree(99999)

    def test_invalid_pgrep_output(self):
        """Test handling invalid pgrep output."""
        with patch("subprocess.run") as mock_run:
            with patch("os.kill"):
                # Mock pgrep returning garbage
                mock_run.return_value = MagicMock(stdout="not a number\n")

                from soupawhisper.lock import _kill_process_tree

                # Should not raise (ValueError caught)
                _kill_process_tree(1000)

    def test_subprocess_error(self):
        """Test handling subprocess errors."""
        import subprocess

        with patch("soupawhisper.lock.subprocess.run", side_effect=subprocess.SubprocessError("pgrep failed")):
            from soupawhisper.lock import _kill_process_tree

            # Should not raise (SubprocessError is caught)
            _kill_process_tree(1000)


class TestAcquireLock:
    """Tests for acquire_lock function."""

    @pytest.fixture
    def temp_lock_file(self):
        """Create temporary lock file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "test.lock"
            with patch("soupawhisper.lock.LOCK_FILE", lock_file):
                yield lock_file

    def test_no_existing_lock(self, temp_lock_file):
        """Test acquiring lock when no existing lock."""
        with patch("atexit.register"):
            from soupawhisper.lock import acquire_lock

            result = acquire_lock()

            assert result is True
            assert temp_lock_file.exists()
            assert temp_lock_file.read_text() == str(os.getpid())

    def test_existing_lock_running_process(self, temp_lock_file):
        """Test acquiring lock when existing process is running."""
        # Write a fake PID
        temp_lock_file.write_text("12345")

        with patch("os.kill") as mock_kill:
            with patch("soupawhisper.lock._kill_process_tree") as mock_kill_tree:
                with patch("time.sleep"):
                    with patch("atexit.register"):
                        # First kill(pid, 0) succeeds (process exists)
                        # Second kill(pid, 0) raises OSError (process terminated)
                        mock_kill.side_effect = [None, OSError("No such process")]

                        from soupawhisper.lock import acquire_lock

                        result = acquire_lock()

                        assert result is True
                        mock_kill_tree.assert_called_once_with(12345)

    def test_existing_lock_dead_process(self, temp_lock_file):
        """Test acquiring lock when existing process is dead."""
        temp_lock_file.write_text("12345")

        with patch("os.kill", side_effect=OSError("No such process")):
            with patch("atexit.register"):
                from soupawhisper.lock import acquire_lock

                result = acquire_lock()

                assert result is True
                # Should have overwritten with new PID
                assert temp_lock_file.read_text() == str(os.getpid())

    def test_invalid_pid_in_lock(self, temp_lock_file):
        """Test handling invalid PID in lock file."""
        temp_lock_file.write_text("not a number")

        with patch("atexit.register"):
            from soupawhisper.lock import acquire_lock

            result = acquire_lock()

            assert result is True
            assert temp_lock_file.read_text() == str(os.getpid())

    def test_force_kill_after_timeout(self, temp_lock_file):
        """Test SIGKILL sent if process doesn't terminate."""
        temp_lock_file.write_text("12345")

        with patch("os.kill") as mock_kill:
            with patch("soupawhisper.lock._kill_process_tree"):
                with patch("time.sleep"):
                    with patch("atexit.register"):
                        # Process never terminates (all kill(pid, 0) succeed)
                        # Then SIGKILL is sent
                        mock_kill.return_value = None  # All calls succeed

                        from soupawhisper.lock import acquire_lock

                        acquire_lock()

                        # Should have called SIGKILL
                        calls = mock_kill.call_args_list
                        sigkill_calls = [c for c in calls if len(c[0]) > 1 and c[0][1] == signal.SIGKILL]
                        assert len(sigkill_calls) > 0

    def test_creates_parent_directory(self):
        """Test lock file parent directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "subdir" / "test.lock"
            with patch("soupawhisper.lock.LOCK_FILE", lock_file):
                with patch("atexit.register"):
                    from soupawhisper.lock import acquire_lock

                    acquire_lock()

                    assert lock_file.parent.exists()

    def test_registers_atexit(self, temp_lock_file):
        """Test atexit handler is registered."""
        with patch("atexit.register") as mock_register:
            from soupawhisper.lock import acquire_lock, release_lock

            acquire_lock()

            mock_register.assert_called_once_with(release_lock)


class TestReleaseLock:
    """Tests for release_lock function."""

    def test_lock_exists(self):
        """Test releasing existing lock file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "test.lock"
            lock_file.write_text("12345")

            with patch("soupawhisper.lock.LOCK_FILE", lock_file):
                from soupawhisper.lock import release_lock

                release_lock()

                assert not lock_file.exists()

    def test_lock_not_exists(self):
        """Test releasing when lock file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "nonexistent.lock"

            with patch("soupawhisper.lock.LOCK_FILE", lock_file):
                from soupawhisper.lock import release_lock

                # Should not raise
                release_lock()

    def test_deletion_fails(self):
        """Test handling when deletion fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "test.lock"
            lock_file.write_text("12345")

            with patch("soupawhisper.lock.LOCK_FILE", lock_file):
                with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
                    from soupawhisper.lock import release_lock

                    # Should not raise
                    release_lock()
