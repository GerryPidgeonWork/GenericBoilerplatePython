# ====================================================================================================
# C12_data_audit.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable DataFrame comparison and reconciliation tools.
#
# Purpose:
#   - Identify mismatches, missing rows, and column-level discrepancies between datasets.
#   - Support structured auditing for reconciliation and validation workflows.
#   - Ensure all audits are logged using the central logging framework.
#
# Usage:
#   from core.C12_data_audit import *
#
# Example:
#   >>> diffs = compare_dataframes(df_je, df_dwh, on="order_id", cols=["amount"])
#   >>> missing = get_missing_rows(df_je, df_dwh, on="order_id")
#   >>> reconcile_column_sums(df_je, df_dwh, "amount", label_a="JE", label_b="DWH")
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
from core.C06_validation_utils import validate_required_columns, validate_non_empty

# ====================================================================================================
# 3. ROW & COLUMN COMPARISON UTILITIES
# ----------------------------------------------------------------------------------------------------
def get_missing_rows(df_a: pd.DataFrame, df_b: pd.DataFrame, on: str) -> pd.DataFrame:
    """
    Identify rows present in df_a but not in df_b based on a key column.

    Args:
        df_a (pd.DataFrame): Source DataFrame A.
        df_b (pd.DataFrame): Comparison DataFrame B.
        on (str): Column to use as the join key.

    Returns:
        pd.DataFrame: Subset of df_a rows missing in df_b.
    """
    try:
        missing = df_a[~df_a[on].isin(df_b[on])]
        logger.info(f"🚫 Found {len(missing)} missing rows in df_b (key='{on}').")
        return missing
    except Exception as e:
        log_exception(e, context="get_missing_rows")
        raise


def compare_dataframes(df_a: pd.DataFrame, df_b: pd.DataFrame, on: str, cols: List[str]) -> pd.DataFrame:
    """
    Compare specific columns between two DataFrames and identify mismatches.

    Args:
        df_a (pd.DataFrame): First DataFrame (e.g. source system).
        df_b (pd.DataFrame): Second DataFrame (e.g. reference system).
        on (str): Join key column name.
        cols (List[str]): List of columns to compare.

    Returns:
        pd.DataFrame: DataFrame showing mismatched records and value differences.
    """
    try:
        merged = pd.merge(df_a, df_b, on=on, how="inner", suffixes=("_a", "_b"))
        diffs = []

        for col in cols:
            col_a, col_b = f"{col}_a", f"{col}_b"
            mismatched = merged[merged[col_a] != merged[col_b]]
            if len(mismatched):
                logger.warning(f"⚠️  {len(mismatched)} mismatched values in '{col}'.")
                diffs.append(mismatched[[on, col_a, col_b]])

        if diffs:
            result = pd.concat(diffs, axis=0).reset_index(drop=True)
            logger.info(f"🧾 Total mismatched records: {len(result)}")
            return result
        else:
            logger.info("✅ No mismatches found between compared columns.")
            return pd.DataFrame(columns=[on] + [f"{c}_a" for c in cols] + [f"{c}_b" for c in cols])

    except Exception as e:
        log_exception(e, context="compare_dataframes")
        raise


def reconcile_column_sums(df_a: pd.DataFrame, df_b: pd.DataFrame, column: str,
                          label_a: str = "A", label_b: str = "B") -> pd.DataFrame:
    """
    Compare total sums of a numeric column across two DataFrames.

    Args:
        df_a (pd.DataFrame): First DataFrame.
        df_b (pd.DataFrame): Second DataFrame.
        column (str): Column to sum and compare.
        label_a (str, optional): Label for DataFrame A. Defaults to "A".
        label_b (str, optional): Label for DataFrame B. Defaults to "B".

    Returns:
        pd.DataFrame: Summary table showing sums, variance, and percent difference.
    """
    try:
        sum_a = df_a[column].sum()
        sum_b = df_b[column].sum()
        variance = sum_a - sum_b
        pct_diff = (variance / sum_b * 100) if sum_b != 0 else np.nan

        summary = pd.DataFrame({
            "DataFrame": [label_a, label_b, "Δ Variance"],
            "Sum": [sum_a, sum_b, variance],
            "% Difference": [np.nan, np.nan, pct_diff]
        })

        logger.info(f"💰 {column}: {label_a}={sum_a:.2f}, {label_b}={sum_b:.2f}, Δ={variance:.2f} ({pct_diff:.2f}%)")
        return summary
    except Exception as e:
        log_exception(e, context="reconcile_column_sums")
        raise


# ====================================================================================================
# 4. AUDIT SUMMARY UTILITIES
# ----------------------------------------------------------------------------------------------------
def summarise_differences(df_diffs: pd.DataFrame, key_col: str) -> Dict[str, int]:
    """
    Produce a simple summary count of mismatched records by key.

    Args:
        df_diffs (pd.DataFrame): DataFrame of mismatched records.
        key_col (str): Key column name used in comparison.

    Returns:
        Dict[str, int]: Summary of mismatched records by key.
    """
    if df_diffs.empty:
        return {"mismatches": 0}
    summary = {"mismatches": len(df_diffs), "unique_keys": df_diffs[key_col].nunique()}
    logger.info(f"🧮 Summary: {summary}")
    return summary


def log_audit_summary(source_name: str, target_name: str,
                      missing_count: int, mismatch_count: int) -> None:
    """
    Log a structured reconciliation summary between two data sources.

    Args:
        source_name (str): Name of the source system (e.g. 'JE').
        target_name (str): Name of the target system (e.g. 'DWH').
        missing_count (int): Number of rows missing in the target.
        mismatch_count (int): Number of value mismatches.
    """
    logger.info("------------------------------------------------------------")
    logger.info(f"🔍 Audit Summary: {source_name} → {target_name}")
    logger.info(f"   Missing in {target_name}: {missing_count}")
    logger.info(f"   Value mismatches:        {mismatch_count}")
    logger.info("------------------------------------------------------------")


# ====================================================================================================
# 5. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone sandboxed test for all data audit utilities.
    No real files are touched.
    """
    print("🔍 Running C12_data_audit self-test...")

    # --- Example mock DataFrames ---
    df_a = pd.DataFrame({
        "order_id": [1, 2, 3, 4],
        "amount": [100, 200, 300, 400]
    })

    df_b = pd.DataFrame({
        "order_id": [2, 3, 4, 5],
        "amount": [200, 350, 400, 500]
    })

    # --- Run checks ---
    missing = get_missing_rows(df_a, df_b, on="order_id")
    diffs = compare_dataframes(df_a, df_b, on="order_id", cols=["amount"])
    summary = reconcile_column_sums(df_a, df_b, "amount", label_a="A", label_b="B")

    log_audit_summary("A", "B", len(missing), len(diffs))
    logger.info(f"\n{summary}")

    print("✅ Data audit utilities sandboxed test complete.")
