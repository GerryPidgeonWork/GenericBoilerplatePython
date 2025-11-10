# ====================================================================================================
# C09_io_utils.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable file input/output utilities for GenericBoilerplatePython projects.
#
# Purpose:
#   - Read and write CSV, JSON, and Excel files with consistent logging and validation.
#   - Ensure directories exist before writing.
#   - Add automatic timestamped backups when overwriting existing files.
#   - Integrate with core logging, validation, and date utilities.
#
# Usage:
#   from core.C09_io_utils import read_csv_file, save_dataframe, save_json, get_latest_file
#
# Example:
#   df = read_csv_file("data/input/orders.csv")
#   save_dataframe(df, "outputs/orders_cleaned.csv")
#
# ----------------------------------------------------------------------------------------------------
# Author:       Gerry Pidgeon
# Created:      2025-11-10
# Project:      GenericBoilerplatePython
# ====================================================================================================


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
from core.C06_validation_utils import validate_directory_exists, validate_file_exists
from core.C07_datetime_utils import timestamp_now                # For backup naming

# ====================================================================================================
# 3. CSV UTILITIES
# ----------------------------------------------------------------------------------------------------
def read_csv_file(file_path: str | Path, **kwargs) -> pd.DataFrame:
    """
    Safely read a CSV file with logging and validation.

    Args:
        file_path (str | Path):
            Path to the CSV file.
        **kwargs:
            Additional keyword arguments passed to `pandas.read_csv()`.

    Returns:
        pd.DataFrame:
            Loaded DataFrame.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        pd.errors.EmptyDataError:
            If the file is empty.
        Exception:
            For other unexpected read errors.
    """
    try:
        validate_file_exists(file_path)
        df = pd.read_csv(file_path, **kwargs)
        logger.info(f"📄 Loaded CSV: {file_path} ({len(df):,} rows, {len(df.columns)} columns)")
        return df
    except Exception as e:
        log_exception(e, context=f"Reading CSV file: {file_path}")
        raise


def save_dataframe(df: pd.DataFrame, file_path: str | Path, overwrite: bool = True, backup_existing: bool = True, **kwargs) -> None:
    """
    Save a DataFrame to a CSV file, with optional overwrite and backup protection.

    Args:
        df (pd.DataFrame):
            DataFrame to save.
        file_path (str | Path):
            Output file path.
        overwrite (bool, optional):
            If False, adds timestamp to avoid overwriting. Defaults to True.
        backup_existing (bool, optional):
            If True, creates a timestamped backup of any existing file before overwriting.
        **kwargs:
            Additional arguments for `DataFrame.to_csv()`.

    Returns:
        None
    """
    path = Path(file_path)
    validate_directory_exists(path.parent, create_if_missing=True)

    # Backup existing file if necessary
    if path.exists() and backup_existing:
        backup_path = path.with_name(f"{path.stem}_backup_{timestamp_now()}{path.suffix}")
        shutil.copy2(path, backup_path)
        logger.warning(f"🗂️  Existing file backed up to: {backup_path}")

    # Handle overwrite policy
    if not overwrite and path.exists():
        path = path.with_name(f"{path.stem}_{timestamp_now()}{path.suffix}")

    try:
        df.to_csv(path, index=False, **kwargs)
        logger.info(f"💾 DataFrame saved to: {path} ({len(df):,} rows)")
    except Exception as e:
        log_exception(e, context=f"Saving DataFrame to {path}")
        raise


# ====================================================================================================
# 4. JSON UTILITIES
# ----------------------------------------------------------------------------------------------------
def read_json(file_path: str | Path, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read a JSON file safely with logging.

    Args:
        file_path (str | Path):
            Path to the JSON file.
        encoding (str, optional):
            Encoding to use. Defaults to 'utf-8'.

    Returns:
        Dict[str, Any]:
            Parsed JSON data.

    Raises:
        FileNotFoundError, json.JSONDecodeError
    """
    try:
        validate_file_exists(file_path)
        with open(file_path, "r", encoding=encoding) as f:
            data = json.load(f)
        logger.info(f"📖 Loaded JSON: {file_path}")
        return data
    except Exception as e:
        log_exception(e, context=f"Reading JSON file: {file_path}")
        raise


def save_json(data: Dict[str, Any], file_path: str | Path, indent: int = 4, overwrite: bool = True) -> None:
    """
    Write JSON data to disk safely, ensuring directory creation.

    Args:
        data (Dict[str, Any]):
            Dictionary or serialisable data to save.
        file_path (str | Path):
            Output path for the JSON file.
        indent (int, optional):
            Number of spaces for indentation. Defaults to 4.
        overwrite (bool, optional):
            If False, adds a timestamp suffix to avoid overwriting.

    Returns:
        None
    """
    path = Path(file_path)
    validate_directory_exists(path.parent, create_if_missing=True)

    if not overwrite and path.exists():
        path = path.with_name(f"{path.stem}_{timestamp_now()}{path.suffix}")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.info(f"💾 JSON file saved: {path}")
    except Exception as e:
        log_exception(e, context=f"Saving JSON file: {path}")
        raise


# ====================================================================================================
# 5. EXCEL UTILITIES
# ----------------------------------------------------------------------------------------------------
def save_excel(df: pd.DataFrame, file_path: str | Path, sheet_name: str = "Sheet1") -> None:
    """
    Save a DataFrame as an Excel file using openpyxl.

    Args:
        df (pd.DataFrame):
            DataFrame to save.
        file_path (str | Path):
            Target Excel file path.
        sheet_name (str, optional):
            Sheet name. Defaults to 'Sheet1'.

    Returns:
        None
    """
    path = Path(file_path)
    validate_directory_exists(path.parent, create_if_missing=True)

    try:
        df.to_excel(path, index=False, sheet_name=sheet_name)
        logger.info(f"📘 Excel file saved: {path}")
    except Exception as e:
        log_exception(e, context=f"Saving Excel file: {path}")
        raise


# ====================================================================================================
# 6. FILE SEARCH & TEXT APPEND
# ----------------------------------------------------------------------------------------------------
def get_latest_file(directory: str | Path, pattern: str = "*.csv") -> Path | None:
    """
    Retrieve the most recently modified file matching a pattern within a directory.

    Args:
        directory (str | Path):
            Directory to search.
        pattern (str, optional):
            Filename pattern (e.g., '*.csv', '*.xlsx'). Defaults to '*.csv'.

    Returns:
        Path | None:
            The path of the most recently modified file, or None if none found.
    """
    path = Path(directory)
    files = list(path.glob(pattern))
    if not files:
        logger.warning(f"⚠️  No files matching {pattern} in {directory}")
        return None

    latest = max(files, key=lambda f: f.stat().st_mtime)
    logger.info(f"🕒 Latest file found: {latest}")
    return latest


def append_to_file(file_path: str | Path, text: str, newline: bool = True) -> None:
    """
    Append text to a file, creating it if it doesn't exist.

    Args:
        file_path (str | Path):
            Path of the file to append to.
        text (str):
            Text to append.
        newline (bool, optional):
            Whether to add a newline after the text. Defaults to True.

    Returns:
        None
    """
    path = Path(file_path)
    validate_directory_exists(path.parent, create_if_missing=True)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + ("\n" if newline else ""))
        logger.info(f"✏️  Appended text to: {path}")
    except Exception as e:
        log_exception(e, context=f"Appending to file: {path}")
        raise


# ====================================================================================================
# 7. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    When run directly, performs a sandboxed I/O test in a temporary directory.
    No files or folders will persist after completion.
    """
    print("🔍 Running C09_io_utils self-test (sandboxed)...")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        logger.info(f"🧪 Temporary test directory: {tmp_path}")

        # --- Create sample DataFrame ---
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        # --- Test CSV save/load ---
        csv_path = tmp_path / "sample.csv"
        save_dataframe(df, csv_path)
        read_csv_file(csv_path)

        # --- Test JSON save/load ---
        json_path = tmp_path / "sample.json"
        save_json({"example": True, "rows": len(df)}, json_path)
        read_json(json_path)

        # --- Test Excel save ---
        excel_path = tmp_path / "sample.xlsx"
        save_excel(df, excel_path)

        # --- Test text append ---
        txt_path = tmp_path / "log.txt"
        append_to_file(txt_path, "This is a test entry.")
        append_to_file(txt_path, "Second line added.")

        # --- Test latest file lookup ---
        get_latest_file(tmp_path, "*.csv")

        logger.info("🧹 Temporary directory cleaned automatically after exit.")

    print("✅ I/O utilities sandboxed test complete. Check logs for details.")