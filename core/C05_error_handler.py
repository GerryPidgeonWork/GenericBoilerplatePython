# ====================================================================================================
# C05_error_handler.py
# ----------------------------------------------------------------------------------------------------
# Centralised error handling for all GenericBoilerplatePython projects.
#
# Purpose:
#   - Provide a unified error-handling interface for both CLI and GUI applications.
#   - Capture and log all uncaught exceptions via sys.excepthook.
#   - Optionally display user-friendly error popups in Tkinter GUIs.
#   - Support manual error capture with contextual logging.
#
# Usage:
#   from core.C05_error_handler import install_global_exception_hook, handle_error
#
#   install_global_exception_hook()
#   ...
#   try:
#       risky_operation()
#   except Exception as e:
#       handle_error(e, context="During import process")
#
# ----------------------------------------------------------------------------------------------------
# Author:       Gerry Pidgeon
# Created:      2025-11-10
# Project:      GenericBoilerplatePython
# ====================================================================================================


# ====================================================================================================
# 1. SYSTEM IMPORTS
# ----------------------------------------------------------------------------------------------------
# Add parent directory to sys.path so this module can import other "core" packages.
# ====================================================================================================
import sys
from pathlib import Path

# --- Standard block for all modules ---
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))     # Add project root so /core/ is importable from anywhere
sys.dont_write_bytecode = True                                      # Prevent creation of __pycache__ folders

# ====================================================================================================
# 2. PROJECT IMPORTS
# ----------------------------------------------------------------------------------------------------
# Bring in standard libraries and settings from the central import hub.
# Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.
# ====================================================================================================
from core.C00_set_packages import *                                 # Imports all universal packages
from core.C01_set_file_paths import PROJECT_ROOT, LOGS_DIR          # Access project root and log directory
from core.C03_logging_handler import get_logger, log_exception      # Unified logging utilities

# --- Initialise logger ---
logger = get_logger(__name__)

# Other required packages
from C04_config_loader import get_config


# ====================================================================================================
# 3. GLOBAL EXCEPTION HANDLER
# ----------------------------------------------------------------------------------------------------
def handle_error(exception: Exception, context: str = "", fatal: bool = False) -> None:
    """
    Log and optionally display an error, with support for GUI popups and fatal exit.

    Args:
        exception (Exception):
            The caught exception object to handle.
        context (str, optional):
            Optional contextual message describing when/where the error occurred.
        fatal (bool, optional):
            If True, will terminate the program after logging (subject to configuration).

    Returns:
        None

    Raises:
        SystemExit:
            If `fatal=True` and the configuration specifies `exit_on_fatal = True`.

    Logging:
        - Logs full exception details including traceback.
        - Adds contextual information if provided.
        - Logs a "💀 Fatal error" before exiting (if applicable).

    GUI Behaviour:
        - If `CONFIG["error_handling"]["show_gui_popups"] = True`, a Tkinter popup
          will display a user-friendly error message.
        - GUI popups are suppressed automatically if unavailable or if disabled.
    """
    log_exception(exception, context=context)

    # --- GUI popup support (optional) ---
    show_popups = get_config("error_handling", "show_gui_popups", default=False)
    if show_popups:
        try:
            from tkinter import messagebox, Tk
            root = Tk()
            root.withdraw()
            messagebox.showerror(
                "❌ Error",
                f"An unexpected error occurred:\n\n{exception}\n\nSee logs for details.",
            )
            root.destroy()
        except Exception as e:
            logger.warning(f"⚠️  Failed to display error popup: {e}")

    # --- Exit on fatal error if configured ---
    exit_on_fatal = get_config("error_handling", "exit_on_fatal", default=False)
    if fatal and exit_on_fatal:
        logger.error("💀 Fatal error encountered. Exiting application.")
        sys.exit(1)


def _exception_hook(exc_type, exc_value, exc_traceback) -> None:
    """
    Custom global exception hook for catching all uncaught exceptions.

    Args:
        exc_type (Type[BaseException]):
            The class (type) of the exception.
        exc_value (BaseException):
            The exception instance itself.
        exc_traceback (traceback):
            The traceback object for the exception.

    Returns:
        None

    Behaviour:
        - Ignores KeyboardInterrupt to allow clean Ctrl+C exits.
        - Logs all other unhandled exceptions via logger and handle_error().
        - Respects fatal exit configuration when applicable.
    """
    # Allow clean termination via Ctrl+C
    if issubclass(exc_type, KeyboardInterrupt):
        logger.info("🛑 Application interrupted by user (Ctrl+C).")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log full traceback for unhandled exceptions
    logger.error("❌ Unhandled Exception", exc_info=(exc_type, exc_value, exc_traceback))
    handle_error(exc_value, context="Unhandled Exception", fatal=True)


def install_global_exception_hook() -> None:
    """
    Install the custom global exception hook for unhandled exceptions.

    This function replaces Python's default `sys.excepthook` with the project-wide
    `_exception_hook()` defined above. Once installed, all unhandled exceptions
    across CLI and GUI scripts will automatically be logged through C03_logging_handler.

    Example:
        >>> from core.C05_error_handler import install_global_exception_hook
        >>> install_global_exception_hook()
    """
    sys.excepthook = _exception_hook
    logger.info("🛡️  Global exception hook installed.")


# ====================================================================================================
# 4. MANUAL TEST FUNCTION
# ----------------------------------------------------------------------------------------------------
def _simulate_error() -> None:
    """
    Simulate an intentional error for validation or demonstration purposes.

    Returns:
        None

    Raises:
        ValueError:
            Always raises a ValueError for testing the error handling pipeline.

    Example:
        >>> _simulate_error()
        ValueError: This is a simulated test exception.
    """
    raise ValueError("This is a simulated test exception.")


# ====================================================================================================
# 5. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    When run directly, verifies that the error handler correctly:
        - Installs the global exception hook.
        - Logs handled exceptions via handle_error().
        - Optionally displays GUI error popups.
        - Handles fatal exit behaviour cleanly.

    Results are logged and printed for manual verification.
    """
    print("🔍 Testing C05_error_handler...")

    install_global_exception_hook()
    logger.info("✅ Global exception hook successfully installed.")

    try:
        _simulate_error()
    except Exception as e:
        handle_error(e, context="During standalone test")

    print("✅ Test complete. Check the logs for output.")
