# ====================================================================================================
# C06_validation_utils.py
# ----------------------------------------------------------------------------------------------------
# Provides shared validation and sanity-check utilities for GenericBoilerplatePython projects.
#
# Purpose:
#   - Centralise all reusable validation logic for files, directories, dataframes, and configuration.
#   - Provide consistent, logged validation across CLI, GUI, and automation contexts.
#   - Ensure early detection of missing inputs, invalid structures, and configuration issues.
#
# Usage:
#   from core.C06_validation_utils import *
#
#   validate_file_exists("data/orders.csv")
#   validate_required_columns(df, ["order_id", "amount", "date"])
#   validate_config_keys("snowflake", ["user", "account"])
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))             # Add project root so /core/ is importable from anywhere
sys.dont_write_bytecode = True                                              # Prevent creation of __pycache__ folders

# ====================================================================================================
# 2. PROJECT IMPORTS
# ----------------------------------------------------------------------------------------------------
# Bring in standard libraries and settings from the central import hub.
# Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.
# ====================================================================================================
from core.C00_set_packages import *                                         # Imports all universal packages
from core.C01_set_file_paths import PROJECT_ROOT, LOGS_DIR, CONFIG_DIR      # Access project root and log directory
from core.C03_logging_handler import get_logger, log_exception              # Unified logging utilities

# --- Initialise logger ---
logger = get_logger(__name__)

# Other required packages
from C04_config_loader import CONFIG


# ====================================================================================================
# 3. FILE & DIRECTORY VALIDATION
# ----------------------------------------------------------------------------------------------------
def validate_file_exists(file_path: str | Path) -> bool:
    """
    Validate that a specified file exists and is accessible.

    Args:
        file_path (str | Path):
            Path to the file to validate.

    Returns:
        bool:
            True if the file exists and is accessible.

    Raises:
        FileNotFoundError:
            If the file does not exist or is not accessible.

    Logging:
        - Logs success (✅) when file exists.
        - Logs error (❌) if the file is missing.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        logger.error(f"❌ File not found: {path}")
        raise FileNotFoundError(f"Required file not found: {path}")
    logger.info(f"✅ File exists: {path}")
    return True


def validate_directory_exists(dir_path: str | Path, create_if_missing: bool = False) -> bool:
    """
    Validate that a directory exists, optionally creating it if missing.

    Args:
        dir_path (str | Path):
            Path to the directory to validate.
        create_if_missing (bool, optional):
            If True, the directory will be created if missing. Defaults to False.

    Returns:
        bool:
            True if the directory exists or was successfully created.

    Raises:
        FileNotFoundError:
            If the directory does not exist and create_if_missing is False.

    Logging:
        - Logs success (✅) when directory exists.
        - Logs warning (📁) when a missing directory is created.
        - Logs error (❌) if the directory is missing and not created.
    """
    path = Path(dir_path)
    if not path.exists():
        if create_if_missing:
            path.mkdir(parents=True, exist_ok=True)
            logger.warning(f"📁 Directory created: {path}")
        else:
            logger.error(f"❌ Directory not found: {path}")
            raise FileNotFoundError(f"Directory not found: {path}")
    else:
        logger.info(f"✅ Directory exists: {path}")
    return True


# ====================================================================================================
# 4. DATA VALIDATION (PANDAS)
# ----------------------------------------------------------------------------------------------------
def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """
    Ensure all required columns are present in a pandas DataFrame.

    Args:
        df (pd.DataFrame):
            The DataFrame to check.
        required_cols (List[str]):
            List of column names that must be present in the DataFrame.

    Returns:
        bool:
            True if all columns exist.

    Raises:
        ValueError:
            If one or more required columns are missing.

    Logging:
        - Logs success (✅) if all required columns are found.
        - Logs error (❌) listing any missing columns.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"❌ Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    logger.info("✅ All required columns present.")
    return True


def validate_non_empty(data: Any, label: str = "Data") -> bool:
    """
    Verify that a dataset (DataFrame, list, or dictionary) is not empty or None.

    Args:
        data (Any):
            The dataset to check (can be a list, dict, pandas DataFrame, etc.).
        label (str, optional):
            Descriptive label for the dataset used in log messages. Defaults to "Data".

    Returns:
        bool:
            True if the dataset contains data.

    Raises:
        ValueError:
            If the dataset is empty or None.

    Logging:
        - Logs success (✅) if the dataset is non-empty.
        - Logs error (❌) if empty or None.
    """
    if data is None or (hasattr(data, "__len__") and len(data) == 0):
        logger.error(f"❌ {label} is empty or None.")
        raise ValueError(f"{label} cannot be empty.")
    logger.info(f"✅ {label} contains data.")
    return True


def validate_numeric(df: pd.DataFrame, column: str) -> bool:
    """
    Validate that a specified DataFrame column contains only numeric data.

    Args:
        df (pd.DataFrame):
            The DataFrame to check.
        column (str):
            Column name to validate for numeric type.

    Returns:
        bool:
            True if the column is numeric.

    Raises:
        ValueError:
            If the column contains non-numeric data or does not exist.

    Logging:
        - Logs success (✅) if the column is numeric.
        - Logs error (❌) if non-numeric data is found.
    """
    if column not in df.columns:
        logger.error(f"❌ Column '{column}' not found in DataFrame.")
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    if not pd.api.types.is_numeric_dtype(df[column]):
        logger.error(f"❌ Column '{column}' contains non-numeric data.")
        raise ValueError(f"Column '{column}' must contain numeric values.")
    logger.info(f"✅ Column '{column}' is numeric.")
    return True


# ====================================================================================================
# 5. CONFIGURATION VALIDATION
# ----------------------------------------------------------------------------------------------------
def validate_config_keys(section: str, keys: List[str]) -> bool:
    """
    Verify that required configuration keys exist within a given configuration section.

    Args:
        section (str):
            Configuration section name (e.g., "snowflake").
        keys (List[str]):
            List of required configuration keys to check for presence.

    Returns:
        bool:
            True if all required keys exist within the section.

    Raises:
        KeyError:
            If any of the required keys are missing.

    Logging:
        - Logs success (✅) when all keys are found.
        - Logs error (❌) listing any missing keys.
    """
    section_data = CONFIG.get(section, {})
    missing = [key for key in keys if key not in section_data]
    if missing:
        logger.error(f"❌ Missing configuration keys in section '{section}': {missing}")
        raise KeyError(f"Missing configuration keys in section '{section}': {missing}")
    logger.info(f"✅ All required config keys found in section '{section}'.")
    return True


# ====================================================================================================
# 6. AGGREGATED VALIDATION REPORT
# ----------------------------------------------------------------------------------------------------
def validation_report(results: Dict[str, bool]) -> None:
    """
    Generate and log a structured validation summary report.

    Args:
        results (Dict[str, bool]):
            Dictionary mapping validation test names to Boolean results (True = pass, False = fail).

    Returns:
        None

    Logging:
        - Logs a concise table of validation outcomes.
        - Each entry includes the test name and PASS/FAIL indicator.
    """
    logger.info("🧾 Validation Summary Report:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f" - {name.ljust(30)} : {status}")


# ====================================================================================================
# 7. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone self-test verifying validation functions across:
        - File/directory existence
        - DataFrame integrity
        - Configuration validation

    Results are logged and printed for quick verification.
    """
    print("🔍 Running C06_validation_utils test...")

    # --- File and directory validation ---
    try:
        validate_directory_exists("test_dir", create_if_missing=True)
        temp_file = Path("test_dir") / "test.csv"
        temp_file.write_text("col1,col2\n1,2")
        validate_file_exists(temp_file)
    except Exception as e:
        log_exception(e, context="File/Directory validation")

    # --- DataFrame validation ---
    try:
        df = pd.DataFrame({"order_id": [1, 2], "amount": [10.5, 20.0]})
        validate_required_columns(df, ["order_id", "amount"])
        validate_non_empty(df, label="Orders DataFrame")
        validate_numeric(df, "amount")
    except Exception as e:
        log_exception(e, context="Data validation")

    # --- Config validation (optional) ---
    try:
        validate_config_keys("snowflake", ["user", "account"])
    except Exception as e:
        log_exception(e, context="Config validation")

    print("✅ Validation tests complete. Check logs for results.")
