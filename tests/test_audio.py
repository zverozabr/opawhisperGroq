"""Tests for AudioRecorder."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


from soupawhisper.audio import AudioDevice, AudioRecorder, _get_record_command


class TestGetRecordCommand:
    """Tests for _get_record_command function."""

    def test_linux_default_device(self):
        """Test Linux command with default device."""
        with patch.object(sys, "platform", "linux"):
            cmd = _get_record_command("/tmp/out.wav", "default")

            assert cmd[0] == "arecord"
            assert "-f" in cmd
            assert "S16_LE" in cmd
            assert "-r" in cmd
            assert "16000" in cmd
            assert "-c" in cmd
            assert "1" in cmd
            assert "/tmp/out.wav" in cmd
            # Default device should not add -D flag
            assert "-D" not in cmd

    def test_linux_specific_device(self):
        """Test Linux command with specific device."""
        with patch.object(sys, "platform", "linux"):
            cmd = _get_record_command("/tmp/out.wav", "hw:1,0")

            assert "-D" in cmd
            assert "hw:1,0" in cmd

    def test_macos_command(self):
        """Test macOS command."""
        with patch.object(sys, "platform", "darwin"):
            cmd = _get_record_command("/tmp/out.wav", "default")

            assert cmd[0] == "rec"
            assert "-r" in cmd
            assert "16000" in cmd
            assert "-c" in cmd
            assert "1" in cmd
            assert "-b" in cmd
            assert "16" in cmd
            assert "/tmp/out.wav" in cmd

    def test_windows_command(self):
        """Test Windows command."""
        with patch.object(sys, "platform", "win32"):
            cmd = _get_record_command("/tmp/out.wav", "default")

            assert cmd[0] == "ffmpeg"
            assert "-y" in cmd
            assert "-f" in cmd
            assert "dshow" in cmd
            assert "-ar" in cmd
            assert "16000" in cmd
            assert "-ac" in cmd
            assert "1" in cmd
            assert "/tmp/out.wav" in cmd

    def test_windows_specific_device(self):
        """Test Windows command with specific device."""
        with patch.object(sys, "platform", "win32"):
            cmd = _get_record_command("/tmp/out.wav", "USB Mic")

            assert "audio=USB Mic" in " ".join(cmd)


class TestAudioRecorder:
    """Tests for AudioRecorder class."""

    def test_init_default_device(self):
        """Test initialization with default device."""
        recorder = AudioRecorder()

        assert recorder._device == "default"
        assert not recorder.is_recording
        assert recorder.file_path is None

    def test_init_custom_device(self):
        """Test initialization with custom device."""
        recorder = AudioRecorder(device="hw:1,0")

        assert recorder._device == "hw:1,0"

    def test_start_creates_temp_file(self):
        """Test that start() creates a temp file and starts process."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()

            assert recorder.is_recording
            assert recorder.file_path is not None
            assert recorder.file_path.suffix == ".wav"
            mock_popen.assert_called_once()

            # Cleanup
            recorder._process = None
            if recorder._temp_file and recorder._temp_file.exists():
                recorder._temp_file.unlink()

    def test_start_does_nothing_if_recording(self):
        """Test that start() is no-op when already recording."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()
            first_file = recorder.file_path

            # Start again
            recorder.start()

            # Should not create new process
            assert mock_popen.call_count == 1
            assert recorder.file_path == first_file

            # Cleanup
            recorder._process = None
            if recorder._temp_file and recorder._temp_file.exists():
                recorder._temp_file.unlink()

    def test_stop_returns_file_path(self):
        """Test that stop() terminates process and returns file path."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()
            expected_path = recorder.file_path

            result = recorder.stop()

            assert result == expected_path
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once()
            assert not recorder.is_recording

            # Cleanup
            if expected_path and expected_path.exists():
                expected_path.unlink()

    def test_stop_returns_none_when_not_recording(self):
        """Test that stop() returns None when not recording."""
        recorder = AudioRecorder()

        result = recorder.stop()

        assert result is None

    def test_cleanup_removes_temp_file(self):
        """Test that cleanup() removes the temp file."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()
            temp_file = recorder.file_path

            # Create actual file for cleanup test
            temp_file.write_bytes(b"test")
            assert temp_file.exists()

            recorder._process = None  # Simulate stopped
            recorder.cleanup()

            assert not temp_file.exists()
            assert recorder._temp_file is None

    def test_cleanup_handles_missing_file(self):
        """Test that cleanup() handles already-deleted file."""
        recorder = AudioRecorder()
        recorder._temp_file = Path("/tmp/nonexistent_file_12345.wav")

        # Should not raise (file doesn't exist, so nothing to clean)
        recorder.cleanup()

        # _temp_file is only set to None if file existed and was deleted
        # If file didn't exist, the method is a no-op
        assert recorder._temp_file is not None  # File didn't exist, so not reset


class TestAudioDevice:
    """Tests for AudioDevice dataclass."""

    def test_audio_device_fields(self):
        """Test AudioDevice stores id and name."""
        device = AudioDevice(id="hw:1,0", name="USB Microphone")

        assert device.id == "hw:1,0"
        assert device.name == "USB Microphone"


class TestListDevices:
    """Tests for AudioRecorder.list_devices()."""

    def test_list_devices_linux(self):
        """Test device listing on Linux."""
        arecord_output = """default
    Default Audio Device
pulse
    PulseAudio Sound Server
hw:0,0
    HDA Intel PCH, ALC887-VD Analog
plughw:1,0
    USB Audio Device"""

        with patch.object(sys, "platform", "linux"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=arecord_output,
                )

                devices = AudioRecorder.list_devices()

                assert len(devices) >= 2
                device_ids = [d.id for d in devices]
                assert "default" in device_ids or "pulse" in device_ids

    def test_list_devices_linux_error(self):
        """Test device listing handles errors gracefully."""
        with patch.object(sys, "platform", "linux"):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                devices = AudioRecorder.list_devices()

                assert devices == []

    def test_list_devices_macos_empty(self):
        """Test macOS returns empty list (no easy enumeration)."""
        with patch.object(sys, "platform", "darwin"):
            devices = AudioRecorder.list_devices()

            assert devices == []

    def test_list_devices_windows(self):
        """Test device listing on Windows."""
        ffmpeg_output = """[dshow @ 0x...] DirectShow audio devices
[dshow @ 0x...]  "Microphone (Realtek)"
[dshow @ 0x...]  "Stereo Mix"
[dshow @ 0x...] DirectShow video devices"""

        with patch.object(sys, "platform", "win32"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,  # ffmpeg returns 1 for list
                    stderr=ffmpeg_output,
                )

                devices = AudioRecorder.list_devices()

                assert len(devices) == 2
                assert devices[0].name == "Microphone (Realtek)"
                assert devices[1].name == "Stereo Mix"
