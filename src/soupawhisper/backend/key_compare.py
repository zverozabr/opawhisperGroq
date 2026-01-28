"""Platform-agnostic key comparison.

This module provides a factory to get the appropriate key comparer
for the current platform. On macOS, pynput returns _darwin.KeyCode
instead of Key enum, requiring vk-based comparison.
"""

import sys
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pynput import keyboard


class KeyComparer(Protocol):
    """Protocol for platform-specific key comparison."""

    def keys_equal(self, pressed: Any, target: "keyboard.Key") -> bool:
        """Check if pressed key matches target hotkey.

        Args:
            pressed: The key received from pynput listener
            target: The target Key enum to compare against

        Returns:
            True if keys match, False otherwise
        """
        ...


def get_key_comparer() -> KeyComparer:
    """Factory: return platform-specific key comparer.

    Returns:
        KeyComparer appropriate for the current platform
    """
    if sys.platform == "darwin":
        from .key_compare_darwin import DarwinKeyComparer

        return DarwinKeyComparer()
    else:
        from .key_compare_default import DefaultKeyComparer

        return DefaultKeyComparer()
