# ====================================================================================================
# C08_string_utils.py
# ----------------------------------------------------------------------------------------------------
# Provides shared string and filename manipulation utilities for GenericBoilerplatePython projects.
#
# Purpose:
#   - Centralise reusable functions for text cleaning, normalization, and safe filename creation.
#   - Support consistent naming conventions across files, GUIs, and data transformations.
#   - Provide lightweight regex-based extraction helpers for IDs, dates, or custom tokens.
#   - Generate filenames prefixed with standardised date formats (daily, monthly, range).
#
# Usage:
#   from core.C08_string_utils import *
#
#   clean = normalize_text("Monthly Report - 25.09.01.pdf")
#   slug  = slugify_filename(clean)
#   dated = generate_dated_filename("Orders Report", ".csv")
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


# ====================================================================================================
# 3. STRING NORMALISATION
# ----------------------------------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """
    Normalize text by:
        - Removing accents and diacritics.
        - Lowercasing all characters.
        - Trimming whitespace.
        - Collapsing internal spaces.

    Args:
        text (str):
            Input string to normalize.

    Returns:
        str:
            Clean, lowercase, accent-free version of the input text.

    Logging:
        - Logs the normalized output for traceability.
    """
    import unicodedata

    if not isinstance(text, str):
        logger.warning(f"⚠️  Expected string, got {type(text)}. Converting to string.")
        text = str(text)

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8", "ignore")
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    logger.debug(f"Normalized text: '{text}'")
    return text


# ====================================================================================================
# 4. FILENAME & SLUG UTILITIES
# ----------------------------------------------------------------------------------------------------
def slugify_filename(filename: str, keep_extension: bool = True) -> str:
    """
    Convert a filename into a filesystem-safe slug.

    Args:
        filename (str):
            Original filename (e.g., 'Monthly Report - 25.09.01.pdf').
        keep_extension (bool, optional):
            If True, preserves the file extension. Defaults to True.

    Returns:
        str:
            Safe, lowercase, underscore-separated filename (e.g., 'monthly_report_250901.pdf').

    Example:
        >>> slugify_filename("Financial Report (Final).PDF")
        'financial_report_final.pdf'

    Logging:
        - Logs final slugified result.
    """
    name, ext = os.path.splitext(filename)
    name = normalize_text(name)
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    result = f"{name}{ext.lower()}" if keep_extension else name
    logger.debug(f"Slugified filename: '{result}'")
    return result


def make_safe_id(text: str, max_length: int = 50) -> str:
    """
    Generate a clean identifier from arbitrary text.

    Args:
        text (str):
            Input text to convert.
        max_length (int, optional):
            Maximum output length. Defaults to 50.

    Returns:
        str:
            Safe lowercase ID (letters, digits, underscores only).

    Example:
        >>> make_safe_id("Generic Boilerplate Project (v1.0)")
        'generic_boilerplate_project_v10'
    """
    text = normalize_text(text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    safe_id = text[:max_length]
    logger.debug(f"Generated safe ID: '{safe_id}'")
    return safe_id


# ====================================================================================================
# 5. REGEX EXTRACTION HELPERS
# ----------------------------------------------------------------------------------------------------
def extract_pattern(text: str, pattern: str, group: int | None = None) -> str | None:
    """
    Extract a substring from text using a regular expression.

    Args:
        text (str):
            Input string to search.
        pattern (str):
            Regular expression pattern to match.
        group (int | None, optional):
            Specific capturing group to return (default = entire match).

    Returns:
        str | None:
            The extracted substring if found, else None.

    Example:
        >>> extract_pattern("OrderID: 12345", r"\\d+")
        '12345'
    """
    match = re.search(pattern, text)
    if not match:
        logger.warning(f"⚠️  Pattern not found in text: {pattern}")
        return None
    result = match.group(group or 0)
    logger.debug(f"Extracted pattern '{pattern}' -> '{result}'")
    return result


# ====================================================================================================
# 6a. GENERIC FILENAME CLEANER
# ----------------------------------------------------------------------------------------------------
def clean_filename_generic(original_name: str) -> str:
    """
    Apply generic cleaning and slugification rules to standardise filenames.

    Args:
        original_name (str):
            Raw filename (e.g., 'Monthly Report - 25.09.01.pdf').

    Returns:
        str:
            Cleaned, slugified filename suitable for storage or export.

    Example:
        >>> clean_filename_generic("Financial Report (Final).PDF")
        'financial_report_final.pdf'

    Notes:
        - Removes special characters ((), [], -, etc.)
        - Normalises spacing and lowercase
        - Preserves file extension
        - Does not apply any domain- or provider-specific text replacements
    """
    cleaned = normalize_text(original_name)
    cleaned = re.sub(r"[\(\)\[\]\-]+", " ", cleaned)
    result = slugify_filename(cleaned)
    logger.info(f"🧹 Cleaned generic filename: {result}")
    return result


# ====================================================================================================
# 6b. DATED FILENAME BUILDER
# ----------------------------------------------------------------------------------------------------
def generate_dated_filename(
    descriptor: str,
    extension: str = ".csv",
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    frequency: str = "daily"
) -> str:
    """
    Generate a standardized filename that begins with a date-based prefix.

    Supported formats:
        - Daily:   YY.MM.DD - descriptor.ext
        - Monthly: YY.MM - descriptor.ext
        - Range:   YY.MM.DD - YY.MM.DD - descriptor.ext

    Args:
        descriptor (str):
            Short descriptive name (e.g., 'JE Reconciliation Report').
        extension (str, optional):
            File extension (e.g., '.csv', '.pdf', '.xlsx'). Defaults to '.csv'.
        start_date (datetime.date | None, optional):
            Start date for range filenames. Defaults to today's date.
        end_date (datetime.date | None, optional):
            End date for range filenames. Used only if both start_date and end_date are provided.
        frequency (str, optional):
            'daily', 'monthly', or 'range'. Determines prefix pattern. Defaults to 'daily'.

    Returns:
        str:
            A clean, dated filename string formatted according to the pattern.

    Example:
        >>> generate_dated_filename("JE Orders", ".xlsx")
        '25.11.10 - je_orders.xlsx'

        >>> generate_dated_filename("Monthly Summary", ".csv", frequency="monthly")
        '25.11 - monthly_summary.csv'

        >>> generate_dated_filename(
                "Weekly Reconciliation",
                start_date=dt.date(2025, 11, 1),
                end_date=dt.date(2025, 11, 7)
            )
        '25.11.01 - 25.11.07 - weekly_reconciliation.csv'

    Notes:
        - Date components are always formatted as YY.MM.DD (two-digit year).
        - Automatically uses today's date if start_date is omitted.
        - Ensures safe, lowercase, underscore-separated descriptor.
        - Extension is normalized to lowercase and prefixed with a dot if missing.
    """
    today = dt.date.today()
    start = start_date or today

    if not extension.startswith("."):
        extension = f".{extension}"
    extension = extension.lower()

    descriptor_clean = make_safe_id(descriptor)

    if start_date and end_date:
        prefix = f"{start_date:%y.%m.%d} - {end_date:%y.%m.%d}"
    elif frequency.lower() == "monthly":
        prefix = f"{start:%y.%m}"
    else:
        prefix = f"{start:%y.%m.%d}"

    filename = f"{prefix} - {descriptor_clean}{extension}"
    logger.info(f"🗂️  Generated dated filename: {filename}")
    return filename


# ====================================================================================================
# 7. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone test for string and filename utilities.
    """
    print("🔍 Running C08_string_utils self-test...")

    sample_text = "Monthly Report - 25.09.01.pdf"
    print(f"Original: {sample_text}")
    print(f"Normalized: {normalize_text(sample_text)}")
    print(f"Slugified: {slugify_filename(sample_text)}")
    print(f"Safe ID: {make_safe_id(sample_text)}")
    print(f"Extracted numbers: {extract_pattern(sample_text, r'\\d+')}")
    print(f"Cleaned generic filename: {clean_filename_generic(sample_text)}")

    print("\n--- Date-based Filenames ---")
    print(generate_dated_filename("Daily Report", ".csv"))
    print(generate_dated_filename("Monthly Summary", ".csv", frequency="monthly"))
    print(
        generate_dated_filename(
            "Weekly Reconciliation",
            start_date=dt.date(2025, 11, 1),
            end_date=dt.date(2025, 11, 7)
        )
    )

    print("✅ String utilities test complete. Check logs for details.")
