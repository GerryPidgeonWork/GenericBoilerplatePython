# ====================================================================================================
# C02_system_processes.py
# ----------------------------------------------------------------------------------------------------
# Provides environment detection and user folder resolution utilities.
#
# Purpose:
#   - Detect the user's operating environment (Windows, macOS, WSL, Linux, or iOS).
#   - Dynamically determine the correct default Downloads folder for file operations.
#   - Support cross-platform compatibility for all GenericBoilerplatePython projects.
#
# Usage:
#   from core.C02_system_processes import detect_os, user_download_folder
#
# Example:
#   >>> detect_os()
#   'Windows (WSL)'
#   >>> user_download_folder()
#   WindowsPath('C:/Users/username/Downloads')
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
# (Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.)
# ====================================================================================================
from core.C00_set_packages import *                              # Imports all universal packages
from core.C01_set_file_paths import PROJECT_ROOT, LOGS_DIR        # Access project root and log directory


# ====================================================================================================
# 3. OPERATING SYSTEM DETECTION
# ----------------------------------------------------------------------------------------------------
# Identify which OS or subsystem Python is currently running on.
# Supports Windows, macOS, Linux, WSL, and iOS environments.
# ====================================================================================================

def detect_os() -> str:
    """
    Detect the current operating system or runtime environment.

    Returns:
        str: A descriptive label representing the detected OS environment.

    Possible return values:
        - "Windows"         : Native Windows Python interpreter.
        - "Windows (WSL)"   : Windows Subsystem for Linux (Ubuntu, Debian, etc.).
        - "macOS"           : macOS using the Darwin kernel.
        - "Linux"           : Generic standalone Linux distribution.
        - "iOS"             : Python runtime on iOS (e.g., Pythonista, Pyto).
        - <sys.platform>    : Fallback for unrecognised systems.

    Example:
        >>> detect_os()
        'Windows (WSL)'
    """
    if sys.platform == "win32":
        return "Windows"

    if sys.platform == "darwin":
        import platform
        machine = platform.machine() or ""
        if machine.startswith(("iP",)):  # e.g. iPhone, iPad
            return "iOS"
        return "macOS"

    if sys.platform.startswith("linux"):
        import platform
        release = platform.uname().release.lower()
        if "microsoft" in release or "wsl" in release:
            return "Windows (WSL)"
        return "Linux"

    # Fallback
    return sys.platform


# ====================================================================================================
# 4. USER DOWNLOAD FOLDER DETECTION
# ----------------------------------------------------------------------------------------------------
# Determines the correct "Downloads" folder depending on OS type.
# Provides a platform-agnostic way to locate the user’s default download directory.
# ====================================================================================================

def user_download_folder() -> Path:
    """
    Returns the current user's "Downloads" folder as a Path object.

    This function accounts for Windows, macOS, Linux, and WSL environments.
    For iOS, it returns the app’s document root (sandboxed).

    Returns:
        Path: The resolved path to the user's Downloads folder.

    Example:
        >>> user_download_folder()
        WindowsPath('C:/Users/username/Downloads')
    """
    os_type = detect_os()
    home = Path.home()

    # --- Windows native ---
    if os_type == "Windows":
        return home / "Downloads"

    # --- Windows Subsystem for Linux (WSL) ---
    if os_type == "Windows (WSL)":
        try:
            linux_user = getpass.getuser()
            win_path_guess = Path(f"/mnt/c/Users/{linux_user}/Downloads")
            if win_path_guess.exists():
                return win_path_guess

            wsl_linux_downloads = home / "Downloads"
            wsl_linux_downloads.mkdir(exist_ok=True)
            return wsl_linux_downloads

        except Exception:
            return home / "Downloads"

    # --- macOS ---
    if os_type == "macOS":
        return home / "Downloads"

    # --- Linux ---
    if os_type == "Linux":
        return home / "Downloads"

    # --- iOS ---
    if os_type == "iOS":
        return home  # No real Downloads folder on iOS sandbox

    # --- Fallback ---
    return home


# ====================================================================================================
# 5. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Allows the module to be run directly for verification.
    Displays detected OS and resolved Downloads folder.
    """
    print(f"Detected OS: {detect_os()}")
    print(f"Download folder: {user_download_folder()}")