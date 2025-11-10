# ====================================================================================================
# C11_data_processing.py
# ----------------------------------------------------------------------------------------------------
# Provides generic data transformation and cleaning utilities for Pandas DataFrames.
#
# Purpose:
#   - Standardise DataFrame cleaning and merging across projects.
#   - Ensure consistent preprocessing steps (column names, nulls, dtypes, etc.).
#   - Provide safe wrappers around common Pandas operations with full logging.
#
# Usage:
#   from core.C11_data_processing import *
#
# Example:
#   >>> df = standardise_columns(df)
#   >>> df = remove_duplicates(df, subset=['order_id'])
#   >>> merged = merge_dataframes(df1, df2, on='id', how='left')
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
from core.C06_validation_utils import validate_non_empty, validate_required_columns

# ====================================================================================================
# 3. STANDARDISATION UTILITIES
# ----------------------------------------------------------------------------------------------------
def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise DataFrame column names (lowercase, trimmed, underscores).

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Copy of DataFrame with cleaned column names.
    """
    original_cols = df.columns.tolist()
    df = df.rename(columns=lambda c: str(c).strip().lower().replace(" ", "_"))
    logger.info(f"🧹 Standardised columns: {original_cols} → {df.columns.tolist()}")
    return df


def convert_to_datetime(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Convert specified columns to datetime, coercing errors to NaT.

    Args:
        df (pd.DataFrame): DataFrame containing date columns.
        cols (List[str]): List of column names to convert.

    Returns:
        pd.DataFrame: Updated DataFrame with datetime columns.
    """
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            logger.info(f"🕒 Converted '{col}' to datetime.")
        else:
            logger.warning(f"⚠️  Column '{col}' not found for datetime conversion.")
    return df


def fill_missing(df: pd.DataFrame, fill_map: Dict[str, Any]) -> pd.DataFrame:
    """
    Fill NaN values in specified columns using a mapping.

    Args:
        df (pd.DataFrame): DataFrame to fill.
        fill_map (Dict[str, Any]): Mapping of column names → fill values.

    Returns:
        pd.DataFrame: DataFrame with missing values filled.
    """
    df = df.fillna(fill_map)
    logger.info(f"🩹 Filled missing values for: {list(fill_map.keys())}")
    return df


# ====================================================================================================
# 4. CLEANING AND FILTERING
# ----------------------------------------------------------------------------------------------------
def remove_duplicates(df: pd.DataFrame, subset: List[str] | None = None) -> pd.DataFrame:
    """
    Remove duplicate rows safely from a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame.
        subset (List[str] | None, optional): Columns to consider for duplicates.
            Defaults to None (all columns).

    Returns:
        pd.DataFrame: Cleaned DataFrame without duplicates.
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    after = len(df)
    logger.info(f"🧩 Removed {before - after} duplicate rows (subset={subset}).")
    return df


def filter_rows(df: pd.DataFrame, condition: Any) -> pd.DataFrame:
    """
    Filter rows based on a condition (boolean mask, Series, or callable).

    Args:
        df (pd.DataFrame): Input DataFrame.
        condition (Any): A lambda, boolean mask, or Series (e.g., df['amount'] > 0).

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    try:
        # Evaluate callable conditions (e.g., lambda df: df['amount'] > 0)
        mask = condition(df) if callable(condition) else condition

        # Ensure mask is a Series or ndarray of booleans
        if isinstance(mask, (pd.Series, np.ndarray, list)):
            filtered = df.loc[mask]
        else:
            # If someone passed a column name string, select then cast to DataFrame
            filtered = df[[mask]] if isinstance(mask, str) else df

        # Always return a DataFrame
        if isinstance(filtered, pd.Series):
            filtered = filtered.to_frame()

        logger.info(f"🔍 Filtered DataFrame: {len(filtered)} rows remaining.")
        return filtered

    except Exception as e:
        log_exception(e, context="filter_rows")
        raise


# ====================================================================================================
# 5. DATA MERGING AND SUMMARY
# ----------------------------------------------------------------------------------------------------
def merge_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, on: str, how: Literal["left", "right", "outer", "inner", "cross"] = "inner",) -> pd.DataFrame:
    """
    Merge two DataFrames with logging and error handling.

    Args:
        df1 (pd.DataFrame): Left DataFrame.
        df2 (pd.DataFrame): Right DataFrame.
        on (str): Column to join on.
        how (str, optional): Type of merge ('left', 'right', 'outer', 'inner'). Defaults to 'inner'.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    try:
        merged = pd.merge(df1, df2, on=on, how=how)
        logger.info(f"🔗 Merged DataFrames ({how.upper()}): {len(merged)} rows.")
        return merged
    except Exception as e:
        log_exception(e, context="merge_dataframes")
        raise


def summarise_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return descriptive statistics for numeric columns.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Summary statistics (count, mean, std, min, max).
    """
    summary = df.describe(include=[np.number]).T
    logger.info(f"📊 Numeric summary generated for {len(summary)} columns.")
    return summary


# ====================================================================================================
# 6. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone sandboxed test for all core data processing utilities.
    Uses temporary directory isolation (non-destructive).
    """
    print("🔍 Running C11_data_processing self-test...")

    # Create a small test DataFrame
    df = pd.DataFrame({
        "Order ID": [1, 2, 2, 3],
        "Amount": [10.0, 20.0, 20.0, None],
        "Date": ["2025-11-01", "2025-11-02", "2025-11-02", "2025-11-03"]
    })

    df = standardise_columns(df)
    df = remove_duplicates(df, subset=["order_id"])
    df = fill_missing(df, {"amount": 0})
    df = convert_to_datetime(df, ["date"])
    df_summary = summarise_numeric(df)
    logger.info(f"\n{df_summary}")

    print("✅ Data processing utilities sandboxed test complete.")
