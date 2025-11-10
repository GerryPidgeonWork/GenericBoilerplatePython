# ====================================================================================================
# C03_logging_handler.py
# ----------------------------------------------------------------------------------------------------
# Provides central logging configuration for all GenericBoilerplatePython projects.
#
# Purpose:
#   - Standardise logging setup (console + file handlers with consistent format).
#   - Automatically create and rotate daily log files in the /logs/ directory.
#   - Support print() redirection into the logging system for complete traceability.
#   - Provide a helper function get_logger(name) for easy access across modules.
#
# Usage:
#   from core.C03_logging_handler import get_logger
#   logger = get_logger(__name__)
#   logger.info("Logging initialised successfully.")
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # Add project root so /core/ is importable from anywhere
sys.dont_write_bytecode = True                                   # Prevent creation of __pycache__ folders

# ====================================================================================================
# 2. PROJECT IMPORTS
# ----------------------------------------------------------------------------------------------------
# Bring in standard libraries and settings from the central import hub.
# Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.
# ====================================================================================================
from core.C00_set_packages import *                              # Imports all universal packages
from core.C01_set_file_paths import PROJECT_ROOT, LOGS_DIR        # Access project root and log directory

# ====================================================================================================
# 3. LOGGING CONFIGURATION
# ----------------------------------------------------------------------------------------------------
# Defines a unified logging format and creates the logs directory if required.
# ====================================================================================================

LOGS_DIR.mkdir(parents=True, exist_ok=True)                      # Ensure logs directory exists
LOG_FILE = LOGS_DIR / f"{dt.datetime.now():%Y-%m-%d}.log"        # Daily rotating log file

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


# ====================================================================================================
# 4. PRINT REDIRECTION (OPTIONAL)
# ----------------------------------------------------------------------------------------------------
# Redirects standard print() output to the logging system.
# This ensures that all console messages are also captured in log files.
# ====================================================================================================

class PrintLogger(io.StringIO):
    """
    Redirects print() output into the logging system while retaining console output.

    Notes:
        - Only non-empty lines are logged.
        - Retains standard print() behaviour.
    """

    def write(self, msg: str) -> int:
        """Write message to both log and stdout buffer."""
        if msg.strip():
            logging.info(msg.strip())
        return super().write(msg)

    def flush(self):
        """Compatibility no-op for stream flush."""
        super().flush()


# --- Enable redirection globally ---
sys.stdout = PrintLogger()


# ====================================================================================================
# 5. LOGGER ACCESS FUNCTION
# ----------------------------------------------------------------------------------------------------
# Provides a convenience wrapper for retrieving named loggers.
# This ensures all modules use the same format and handlers.
# ====================================================================================================

def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a named logger instance configured with the project-wide logging setup.

    Args:
        name (str | None, optional): The logger name (typically __name__). Defaults to None for root logger.

    Returns:
        logging.Logger: A logger object ready for use.

    Example:
        >>> from core.C03_logging_handler import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Initialised logging successfully.")
    """
    return logging.getLogger(name)


# ====================================================================================================
# 6. LOGGER UTILITIES
# ----------------------------------------------------------------------------------------------------
# Helper utilities for common logging tasks (e.g. divider lines and exception tracing).
# ====================================================================================================

def log_divider(level: str = "info", label: str = "", width: int = 80) -> None:
    """
    Writes a visual divider line into the log for readability.

    Args:
        level (str, optional): Log level method (info, warning, error). Defaults to 'info'.
        label (str, optional): Optional text label to centre within the divider.
        width (int, optional): Width of the divider line. Defaults to 80.
    """
    msg = f" {label} " if label else ""
    line = msg.center(width, "-")
    logger = get_logger("divider")
    getattr(logger, level.lower(), logger.info)(line)


def log_exception(e: Exception, context: str = "") -> None:
    """
    Logs an exception with traceback details.

    Args:
        e (Exception): The caught exception object.
        context (str, optional): Description of what was happening when the error occurred.
    """
    logger = get_logger("exception")
    logger.error(f"❌ Exception occurred {context if context else ''}: {e}", exc_info=True)


# ====================================================================================================
# 7. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    When executed directly, verifies logging functionality by writing test entries to the console and log file.
    """
    logger = get_logger(__name__)
    logger.info("🔍 Logging test started")
    log_divider(label="C03 Logging Handler Verification")

    try:
        _ = 1 / 0  # Intentional division-by-zero error
    except Exception as e:
        log_exception(e, context="During sample division test")

    logger.info("✅ Logging test completed successfully.")
    print("This message is also redirected to the log file.")
