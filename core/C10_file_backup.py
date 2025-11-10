# ====================================================================================================
# C10_file_backup.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable backup and restore utilities for GenericBoilerplatePython projects.
#
# Purpose:
#   - Create timestamped file backups before overwriting or modifying important files.
#   - Manage backup retention automatically.
#   - Support restoring specific versions from backup.
#   - Standardise backup naming and logging across projects.
#
# Usage:
#   from core.C10_file_backup import create_backup, list_backups, purge_old_backups, restore_backup
#
# Example:
#   >>> create_backup("data/report.csv")
#   'data/report_backup_20251109_222501.csv'
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
from core.C06_validation_utils import validate_file_exists
from core.C07_datetime_utils import timestamp_now

# ====================================================================================================
# 3. BACKUP CREATION
# ----------------------------------------------------------------------------------------------------
def create_backup(file_path: str | Path) -> Path:
    """
    Create a timestamped backup of the given file in the same directory.

    Args:
        file_path (str | Path): The file to back up.

    Returns:
        Path: Path to the newly created backup file.

    Example:
        >>> create_backup("data/report.csv")
        PosixPath('data/report_backup_20251109_222501.csv')
    """
    try:
        file = Path(file_path)
        validate_file_exists(file)

        timestamp = timestamp_now()
        backup_path = file.with_name(f"{file.stem}_backup_{timestamp}{file.suffix}")
        shutil.copy2(file, backup_path)

        logger.info(f"🧩 Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        log_exception(e, context="create_backup")
        raise


# ====================================================================================================
# 4. BACKUP LISTING
# ----------------------------------------------------------------------------------------------------
def list_backups(file_path: str | Path) -> List[Path]:
    """
    List all backup files associated with a given original file.

    Args:
        file_path (str | Path): Path of the base file.

    Returns:
        List[Path]: Sorted list of matching backup files (newest first).
    """
    file = Path(file_path)
    pattern = f"{file.stem}_backup_*{file.suffix}"
    backups = sorted(file.parent.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)

    logger.info(f"📂 Found {len(backups)} backups for {file.name}")
    return backups


# ====================================================================================================
# 5. BACKUP RETENTION
# ----------------------------------------------------------------------------------------------------
def purge_old_backups(file_path: str | Path, keep_latest: int = 5) -> None:
    """
    Retain only the latest N backups for a given file, deleting older ones.

    Args:
        file_path (str | Path): Base file path to clean up.
        keep_latest (int, optional): Number of most recent backups to retain. Defaults to 5.
    """
    backups = list_backups(file_path)
    if len(backups) <= keep_latest:
        logger.info(f"✅ No cleanup needed. {len(backups)} backup(s) within retention limit.")
        return

    to_delete = backups[keep_latest:]
    for old in to_delete:
        try:
            old.unlink()
            logger.warning(f"🗑️  Deleted old backup: {old}")
        except Exception as e:
            log_exception(e, context=f"purge_old_backups: {old}")

    logger.info(f"♻️  Retained {keep_latest} most recent backups, deleted {len(to_delete)} older ones.")


# ====================================================================================================
# 6. RESTORE BACKUP
# ----------------------------------------------------------------------------------------------------
def restore_backup(file_path: str | Path, backup_file: str | Path) -> bool:
    """
    Restore a file from a selected backup.

    Args:
        file_path (str | Path): Target file path to overwrite.
        backup_file (str | Path): Backup file to restore from.

    Returns:
        bool: True if restored successfully, False otherwise.
    """
    try:
        file = Path(file_path)
        backup = Path(backup_file)
        validate_file_exists(backup)

        shutil.copy2(backup, file)
        logger.info(f"🔄 Restored {file.name} from {backup.name}")
        return True
    except Exception as e:
        log_exception(e, context="restore_backup")
        return False


# ====================================================================================================
# 7. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone test to verify backup creation, listing, retention, and restore operations.
    Uses a sandboxed temporary directory to avoid modifying real files.
    """
    print("🔍 Running C10_file_backup self-test (sandboxed)...")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "sample.txt"
        test_file.write_text("Original content")

        # Create multiple backups
        for _ in range(3):
            create_backup(test_file)
            time.sleep(0.5)

        # List backups
        backups = list_backups(test_file)
        logger.info(f"🧾 Backups found: {backups}")

        # Purge retention (keep latest 2)
        purge_old_backups(test_file, keep_latest=2)

        # Restore from most recent
        if backups:
            restore_backup(test_file, backups[0])

        logger.info("🧹 Temporary directory cleaned automatically after exit.")

    print("✅ File backup utilities sandboxed test complete. Check logs for details.")
