"""Default key comparison for Linux and Windows.

On these platforms, pynput correctly returns Key enum objects,
so direct comparison works.
"""

from typing import Any

from pynput import keyboard


class DefaultKeyComparer:
    """Direct key comparison for Linux and Windows.

    pynput on Linux (X11) and Windows returns Key enum directly,
    so simple equality comparison works.
    """

    def keys_equal(self, pressed: Any, target: keyboard.Key) -> bool:
        """Check if pressed key matches target hotkey.

        Args:
            pressed: The key received from pynput listener
            target: The target Key enum to compare against

        Returns:
            True if keys are equal, False otherwise
        """
        return pressed == target
