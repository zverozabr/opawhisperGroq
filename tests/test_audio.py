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
        """Test macOS command with default device."""
        with patch.object(sys, "platform", "darwin"):
            cmd = _get_record_command("/tmp/out.wav", "default")

            assert cmd[0] == "ffmpeg"
            assert "-y" in cmd
            assert "-f" in cmd
            assert "avfoundation" in cmd
            assert "-ar" in cmd
            assert "16000" in cmd
            assert "-ac" in cmd
            assert "1" in cmd
            assert "/tmp/out.wav" in cmd
            # Default device uses :0
            assert ":0" in cmd

    def test_macos_specific_device(self):
        """Test macOS command with specific device."""
        with patch.object(sys, "platform", "darwin"):
            cmd = _get_record_command("/tmp/out.wav", "2")

            assert ":2" in cmd

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
        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [AudioDevice(id="0", name="Mic")]
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
        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [AudioDevice(id="0", name="Mic")]
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
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()
            expected_path = recorder.file_path

            result = recorder.stop()

            assert result == expected_path
            mock_process.terminate.assert_called_once()
            mock_process.communicate.assert_called_once()
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

    def test_list_devices_macos(self):
        """Test device listing on macOS."""
        ffmpeg_output = """[AVFoundation indev @ 0x...] AVFoundation video devices:
[AVFoundation indev @ 0x...] [0] FaceTime Camera
[AVFoundation indev @ 0x...] AVFoundation audio devices:
[AVFoundation indev @ 0x...] [0] Built-in Microphone
[AVFoundation indev @ 0x...] [1] USB Microphone"""

        with patch.object(sys, "platform", "darwin"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,  # ffmpeg returns 1 for list
                    stderr=ffmpeg_output,
                )

                devices = AudioRecorder.list_devices()

                assert len(devices) == 2
                assert devices[0].id == "0"
                assert devices[0].name == "Built-in Microphone"
                assert devices[1].id == "1"
                assert devices[1].name == "USB Microphone"

    def test_list_devices_macos_error(self):
        """Test macOS device listing handles errors gracefully."""
        with patch.object(sys, "platform", "darwin"):
            with patch("subprocess.run", side_effect=FileNotFoundError):
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


class TestAudioRecorderErrorCapture:
    """Tests for AudioRecorder stderr capture (TDD)."""

    def test_has_last_error_attribute(self):
        """AudioRecorder should have last_error attribute."""
        recorder = AudioRecorder()

        assert hasattr(recorder, "last_error")
        assert recorder.last_error is None

    def test_stop_captures_stderr(self):
        """stop() should capture stderr from ffmpeg."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (b"", b"Some ffmpeg output\n")
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()
            recorder.stop()

            # Should have captured stderr
            assert recorder.last_stderr is not None
            assert "ffmpeg" in recorder.last_stderr.lower()

    def test_stop_handles_timeout(self):
        """stop() should handle communicate timeout gracefully."""
        import subprocess

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 2)
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()
            recorder.start()

            # Should not raise
            recorder.stop()

            # Should have called terminate as fallback
            mock_process.terminate.assert_called()

    def test_stderr_cleared_on_new_recording(self):
        """last_stderr should be cleared when starting new recording."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (b"", b"error1")
            mock_popen.return_value = mock_process

            recorder = AudioRecorder()

            # First recording
            recorder.start()
            recorder.stop()
            assert recorder.last_stderr is not None

            # Second recording should clear
            recorder.start()
            assert recorder.last_stderr is None

            # Cleanup
            recorder._process = None


class TestDeviceResolver:
    """Tests for DeviceResolver class (TDD - tests written before implementation)."""

    def test_default_returns_first_device(self):
        """'default' preference returns first available device."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [
                AudioDevice(id="0", name="Built-in Mic"),
                AudioDevice(id="1", name="USB Mic"),
            ]

            resolver = DeviceResolver(preferred_device="default")
            result = resolver.resolve()

            assert result == "0"

    def test_preferred_device_available(self):
        """Returns preferred device when it exists."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [
                AudioDevice(id="0", name="Built-in Mic"),
                AudioDevice(id="1", name="USB Mic"),
            ]

            resolver = DeviceResolver(preferred_device="1")
            result = resolver.resolve()

            assert result == "1"

    def test_preferred_device_missing_fallback(self):
        """Falls back to default when preferred device missing and cache populated."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [
                AudioDevice(id="0", name="Built-in Mic"),
            ]

            # Populate cache first
            DeviceResolver._cached_devices = mock_list.return_value
            DeviceResolver._cache_valid = True

            resolver = DeviceResolver(preferred_device="1")  # Device 1 not available
            result = resolver.resolve()

            assert result == "0"  # Falls back to first available

            # Cleanup
            DeviceResolver._cache_valid = False

    def test_preferred_device_reconnected(self):
        """Returns preferred device after reconnection when cache updated."""
        from soupawhisper.audio import DeviceResolver

        resolver = DeviceResolver(preferred_device="1")

        # First call: device missing (cache populated with only device 0)
        DeviceResolver._cached_devices = [AudioDevice(id="0", name="Built-in Mic")]
        DeviceResolver._cache_valid = True

        result1 = resolver.resolve()
        assert result1 == "0"  # Fallback

        # Second call: device reconnected (cache updated)
        DeviceResolver._cached_devices = [
            AudioDevice(id="0", name="Built-in Mic"),
            AudioDevice(id="1", name="USB Mic"),
        ]

        result2 = resolver.resolve()
        assert result2 == "1"  # Back to preferred

        # Cleanup
        DeviceResolver._cache_valid = False

    def test_empty_device_list(self):
        """Handles empty device list gracefully."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = []

            resolver = DeviceResolver(preferred_device="default")
            result = resolver.resolve()

            assert result == "0"  # Fallback to "0" when no devices

    def test_is_preferred_available_true(self):
        """is_preferred_available() returns True when device connected."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = [
                AudioDevice(id="0", name="Built-in Mic"),
                AudioDevice(id="1", name="USB Mic"),
            ]

            resolver = DeviceResolver(preferred_device="1")
            assert resolver.is_preferred_available() is True

    def test_is_preferred_available_false(self):
        """is_preferred_available() returns False when device not in cache."""
        from soupawhisper.audio import DeviceResolver

        # Populate cache without the preferred device
        DeviceResolver._cached_devices = [AudioDevice(id="0", name="Built-in Mic")]
        DeviceResolver._cache_valid = True

        resolver = DeviceResolver(preferred_device="1")
        assert resolver.is_preferred_available() is False

        # Cleanup
        DeviceResolver._cache_valid = False

    def test_is_preferred_available_default_always_true(self):
        """is_preferred_available() returns True for 'default' preference."""
        from soupawhisper.audio import DeviceResolver

        with patch.object(AudioRecorder, "list_devices") as mock_list:
            mock_list.return_value = []  # Even with no devices

            resolver = DeviceResolver(preferred_device="default")
            assert resolver.is_preferred_available() is True
