"""MLX Server Manager - manages persistent MLX server process.

Single Responsibility: Manages the lifecycle of the MLX Whisper server process.
Encapsulates global state that was previously scattered in mlx.py module.
"""

import atexit
import json
import logging
import os
import subprocess
import sys
from typing import Optional

from soupawhisper.providers.base import TranscriptionError

logger = logging.getLogger(__name__)


class MLXServerManager:
    """Manages the persistent MLX server process for model caching.
    
    Implements singleton pattern to ensure only one server runs at a time.
    Provides clean API for server lifecycle management.
    
    SOLID/SRP: Single responsibility - server process lifecycle management.
    """
    
    _instance: Optional["MLXServerManager"] = None
    
    def __new__(cls) -> "MLXServerManager":
        """Singleton pattern - only one server manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize server manager (only once due to singleton)."""
        if getattr(self, "_initialized", False):
            return
        
        self._server_process: Optional[subprocess.Popen] = None
        self._server_model_path: Optional[str] = None
        self._initialized = True
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    @property
    def is_running(self) -> bool:
        """Check if MLX server is currently running."""
        return self._server_process is not None and self._server_process.poll() is None
    
    @property
    def loaded_model(self) -> Optional[str]:
        """Get currently loaded model path, or None if server not running."""
        if self.is_running:
            return self._server_model_path
        return None
    
    def shutdown(self) -> None:
        """Shutdown the MLX server gracefully."""
        if self._server_process is None:
            return
        
        try:
            self._server_process.stdin.write('{"command": "shutdown"}\n')
            self._server_process.stdin.flush()
            self._server_process.wait(timeout=5)
        except Exception:
            try:
                self._server_process.kill()
            except Exception:
                pass
        finally:
            self._server_process = None
            self._server_model_path = None
    
    def switch_model(self, new_model_path: str) -> None:
        """Switch to a different model, unloading the current one.
        
        Args:
            new_model_path: Path to the new model to load
        """
        current = self.loaded_model
        if current == new_model_path:
            logger.debug(f"Model {new_model_path} already loaded, no switch needed")
            return
        
        if current:
            logger.info(f"Unloading model: {current}")
        
        # Stop server - this unloads the model from memory
        self.shutdown()
        
        # Set new model path - will be loaded on next ensure_running call
        self._server_model_path = new_model_path
        logger.info(f"Model switched to: {new_model_path} (will load on next use)")
    
    def ensure_running(self, model_path: str) -> subprocess.Popen:
        """Ensure the MLX server process is running with the specified model.
        
        Args:
            model_path: Path or HuggingFace repo of the model to load
        
        Returns:
            The running server subprocess
        
        Raises:
            TranscriptionError: If server fails to start
        """
        # Check if server is running with correct model
        if self._server_process is not None:
            if self._server_process.poll() is not None:
                # Process died, need restart
                logger.info("MLX server died, restarting...")
                self._server_process = None
            elif self._server_model_path != model_path:
                # Model changed, restart server
                logger.info(
                    f"Model changed ({self._server_model_path} -> {model_path}), "
                    "restarting server..."
                )
                self.shutdown()
        
        if self._server_process is None:
            self._start_server(model_path)
        
        return self._server_process
    
    def _start_server(self, model_path: str) -> None:
        """Start the MLX server process.
        
        Args:
            model_path: Path or HuggingFace repo of the model
        
        Raises:
            TranscriptionError: If server fails to start
        """
        logger.info(f"Starting MLX server with model: {model_path}")
        
        # Run as module to ensure proper imports
        self._server_process = subprocess.Popen(
            [sys.executable, "-m", "soupawhisper.providers.mlx_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env={**os.environ},  # Inherit environment for proper library paths
        )
        self._server_model_path = model_path
        
        # Wait for ready signal
        try:
            ready_line = self._server_process.stdout.readline()
            ready = json.loads(ready_line)
            if ready.get("status") != "ready":
                raise TranscriptionError(f"Server not ready: {ready}")
            logger.info("MLX server ready")
        except Exception as e:
            self._server_process.kill()
            self._server_process = None
            self._server_model_path = None
            raise TranscriptionError(f"Failed to start MLX server: {e}") from e
    
    def send_request(self, request: dict) -> dict:
        """Send a request to the server and get response.
        
        Args:
            request: JSON-serializable request dict
        
        Returns:
            Response dict from server
        
        Raises:
            TranscriptionError: If communication fails
        """
        if not self.is_running:
            raise TranscriptionError("Server not running")
        
        try:
            self._server_process.stdin.write(json.dumps(request) + "\n")
            self._server_process.stdin.flush()
            
            response_line = self._server_process.stdout.readline()
            if not response_line:
                raise TranscriptionError("Server returned empty response")
            
            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise TranscriptionError(f"Invalid JSON from server: {e}") from e
        except Exception as e:
            raise TranscriptionError(f"Server communication failed: {e}") from e


# Module-level convenience functions (for backward compatibility)
_manager: Optional[MLXServerManager] = None


def get_server_manager() -> MLXServerManager:
    """Get the singleton server manager instance."""
    global _manager
    if _manager is None:
        _manager = MLXServerManager()
    return _manager


def shutdown_server() -> None:
    """Shutdown the MLX server (public API, backward compatible)."""
    get_server_manager().shutdown()


def get_loaded_model() -> Optional[str]:
    """Get currently loaded model path, or None if server not running."""
    return get_server_manager().loaded_model


def is_server_running() -> bool:
    """Check if MLX server is running."""
    return get_server_manager().is_running


def switch_model(new_model_path: str) -> None:
    """Switch to a different model, unloading the current one."""
    get_server_manager().switch_model(new_model_path)
