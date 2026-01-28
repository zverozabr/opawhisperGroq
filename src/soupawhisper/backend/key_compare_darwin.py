"""macOS-specific key comparison using virtual key codes.

On macOS, pynput returns _darwin.KeyCode instead of Key enum when
a key is pressed. This module compares keys by their vk (virtual key code)
attribute to work around this issue.

See: https://github.com/moses-palmer/pynput/issues/439
"""

from typing import Any

from pynput import keyboard


class DarwinKeyComparer:
    """Compare keys using vk (virtual key code) on macOS.

    pynput on macOS returns _darwin.KeyCode instead of Key enum,
    so we need to compare by vk attribute.
    """

    def keys_equal(self, pressed: Any, target: keyboard.Key) -> bool:
        """Check if pressed key matches target hotkey.

        Args:
            pressed: The key received from pynput listener (_darwin.KeyCode)
            target: The target Key enum to compare against

        Returns:
            True if keys match by vk code, False otherwise
        """
        # Direct match (fallback for rare cases)
        if pressed == target:
            return True

        # Compare by virtual key code
        pressed_vk = getattr(pressed, "vk", None)
        target_value = getattr(target, "value", None)
        target_vk = getattr(target_value, "vk", None) if target_value else None

        if pressed_vk is not None and target_vk is not None:
            return pressed_vk == target_vk

        return False
