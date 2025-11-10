# ====================================================================================================
# C01_set_file_paths.py
# ----------------------------------------------------------------------------------------------------
# Centralises all key file and directory paths for the project.
#
# Purpose:
#   - Define a single source of truth for the project's root directory.
#   - Automatically construct paths for core folders (data, logs, outputs, etc.).
#   - Provide utility functions for safe directory creation and temporary file handling.
#
# Usage:
#   from core.C01_set_file_paths import *
#
# Example:
#   >>> from core.C01_set_file_paths import DATA_DIR, build_path
#   >>> my_file = build_path(DATA_DIR, "inputs", "example.csv")
#   >>> print(my_file)
#   C:\Users\User\Projects\MyProject\data\inputs\example.csv
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


# ====================================================================================================
# 3. PROJECT ROOT
# ----------------------------------------------------------------------------------------------------
# Detects and defines the project's root directory dynamically.
# Works whether running locally, from an IDE, or as a compiled executable.
# ====================================================================================================
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent         # e.g., /.../GenericBoilerplatePython/
except NameError:
    PROJECT_ROOT = Path.cwd()                                     # Fallback for interactive environments

# Useful derived variables
PROJECT_ROOT_STR = str(PROJECT_ROOT)                              # String form for JSON/log usage
PROJECT_NAME     = PROJECT_ROOT.name                              # Name of the current project folder
USER_HOME_DIR    = Path.home()                                    # Path to current user’s home directory

# ====================================================================================================
# 4. CORE DIRECTORIES
# ----------------------------------------------------------------------------------------------------
# Defines the key static folder paths at the project root.
# These correspond to the locked boilerplate folder structure.
# ====================================================================================================
CORE_DIR           = PROJECT_ROOT / "core"
CONFIG_DIR         = PROJECT_ROOT / "config"
CREDENTIALS_DIR    = PROJECT_ROOT / "credentials"
DATA_DIR           = PROJECT_ROOT / "data"
IMPLEMENTATION_DIR = PROJECT_ROOT / "implementation"
LOGS_DIR           = PROJECT_ROOT / "logs"
MAIN_DIR           = PROJECT_ROOT / "main"
OUTPUTS_DIR        = PROJECT_ROOT / "outputs"
SCRATCHPAD_DIR     = PROJECT_ROOT / "scratchpad"
BINARY_FILES_DIR   = PROJECT_ROOT / "binary_files"

# --- Ensure key directories exist (non-destructive) ---
for path in [LOGS_DIR, DATA_DIR, OUTPUTS_DIR, CREDENTIALS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# ====================================================================================================
# 5. GOOGLE DRIVE API FILES
# ----------------------------------------------------------------------------------------------------
# Paths for the Google Drive API credentials.
# C20_google_api_integration.py will look for these files here.
# ====================================================================================================
GDRIVE_DIR = PROJECT_ROOT / "credentials"
GDRIVE_CREDENTIALS_FILE = GDRIVE_DIR / "credentials.json"
GDRIVE_TOKEN_FILE = GDRIVE_DIR / "token.json"

# ====================================================================================================
# 6. GENERIC UTILITIES
# ----------------------------------------------------------------------------------------------------
# Contains helper functions for file path creation, validation, and temporary file generation.
# These are project-agnostic and safe to use in any context.
# ====================================================================================================

def ensure_directory(path: Path) -> Path:
    """
    Ensures that a directory exists, creating it if necessary.

    Args:
        path (Path): The directory path to verify or create.

    Returns:
        Path: The resolved absolute path of the created or existing directory.

    Example:
        >>> from core.C01_set_file_paths import ensure_directory, DATA_DIR
        >>> ensure_directory(DATA_DIR / "exports")
        WindowsPath('C:/Projects/GenericBoilerplatePython/data/exports')
    """
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def build_path(*parts: str | Path) -> Path:
    """
    Safely joins multiple path components and returns a resolved Path object.

    Args:
        *parts (str | Path): Sequence of directory or file components.

    Returns:
        Path: Fully resolved Path object representing the combined location.

    Example:
        >>> from core.C01_set_file_paths import build_path, DATA_DIR
        >>> build_path(DATA_DIR, "inputs", "example.csv")
        WindowsPath('C:/Projects/GenericBoilerplatePython/data/inputs/example.csv')
    """
    return Path(*parts).resolve()


def get_temp_file(suffix: str = "", prefix: str = "temp_", directory: Optional[Path] = None) -> Path:
    """
    Creates and returns a temporary file path within the specified directory (or the system temp folder).

    Args:
        suffix (str, optional): Optional file extension (e.g., '.txt' or '.csv').
        prefix (str, optional): Optional filename prefix (default 'temp_').
        directory (Path, optional): Directory where the file should be created. Defaults to system temp.

    Returns:
        Path: Full path to the temporary file (not yet opened or written).

    Example:
        >>> from core.C01_set_file_paths import get_temp_file
        >>> temp_path = get_temp_file(suffix=".log")
        >>> print(temp_path)
        WindowsPath('C:/Users/User/AppData/Local/Temp/temp_abcd1234.log')
    """

    directory = directory or Path(tempfile.gettempdir())
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=directory)
    os.close(fd)  # ✅ Close file descriptor before deleting
    Path(path).unlink(missing_ok=True)  # Remove empty placeholder file
    return Path(path)

# ====================================================================================================
# 7. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    When run directly, this section prints all key project directories and tests utility functions.
    This allows quick verification that the environment and folder structure are configured correctly.
    """
    print(f"\n🔍 Project Root: {PROJECT_ROOT}")
    print(f"📁 Project Name: {PROJECT_NAME}")
    print(f"🏠 User Home Dir: {USER_HOME_DIR}")
    print("-----------------------------------------------------------")
    print("Core Folders:")
    for name, path in {
        "CORE_DIR": CORE_DIR,
        "CONFIG_DIR": CONFIG_DIR,
        "CREDENTIALS_DIR": CREDENTIALS_DIR,
        "DATA_DIR": DATA_DIR,
        "IMPLEMENTATION_DIR": IMPLEMENTATION_DIR,
        "LOGS_DIR": LOGS_DIR,
        "MAIN_DIR": MAIN_DIR,
        "OUTPUTS_DIR": OUTPUTS_DIR,
        "SCRATCHPAD_DIR": SCRATCHPAD_DIR,
        "BINARY_FILES_DIR": BINARY_FILES_DIR,
    }.items():
        print(f"{name.ljust(25)} : {path}")

    temp_file = get_temp_file(suffix=".txt")
    print(f"\n🧪 Temporary test file path: {temp_file}")