# ====================================================================================================
# C07_datetime_utils.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable date and time helper functions for GenericBoilerplatePython projects.
#
# Purpose:
#   - Standardise date/time manipulation logic across all projects.
#   - Simplify handling of week/month boundaries and common date formatting.
#   - Ensure consistent, locale-agnostic, ISO-style (YYYY-MM-DD) behaviour across scripts.
#
# Usage:
#   from core.C07_datetime_utils import *
#
# Example:
#   >>> get_today()
#   datetime.date(2025, 11, 10)
#   >>> get_start_of_week()
#   datetime.date(2025, 11, 3)
#   >>> get_month_range(2025, 10)
#   (datetime.date(2025, 10, 1), datetime.date(2025, 10, 31))
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
# 3. GLOBAL CONSTANTS
# ----------------------------------------------------------------------------------------------------
DEFAULT_DATE_FORMAT = "%Y-%m-%d"


def as_str(d: date | datetime) -> str:
    """
    Convert a date or datetime object into a formatted string (YYYY-MM-DD).

    Args:
        d (date | datetime): The date or datetime object to convert.

    Returns:
        str: The formatted date string in ISO format (YYYY-MM-DD).

    Raises:
        TypeError: If the provided object is not a date or datetime instance.
    """
    if isinstance(d, (datetime, date)):
        return d.strftime(DEFAULT_DATE_FORMAT)
    raise TypeError("Expected a date or datetime object.")


def timestamp_now(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """
    Return the current timestamp as a compact string for filenames or logs.

    Args:
        fmt (str, optional):
            Datetime format string. Defaults to '%Y%m%d_%H%M%S'.

    Returns:
        str:
            Current local timestamp formatted for safe filename usage (e.g. '20251109_222501').

    Example:
        >>> timestamp_now()
        '20251109_222501'
    """
    return datetime.now().strftime(fmt)

# ====================================================================================================
# 4. BASIC DATE HELPERS
# ----------------------------------------------------------------------------------------------------
def get_today() -> date:
    """
    Return today's local calendar date (no time component).

    Returns:
        date: The current local date as a datetime.date object.
    """
    return date.today()


def get_now() -> datetime:
    """
    Return the current local date and time.

    Returns:
        datetime: A datetime object representing the current local date and time.
    """
    return datetime.now()


def format_date(d: date | datetime, fmt: str = DEFAULT_DATE_FORMAT) -> str:
    """
    Format a date or datetime object as a string.

    Args:
        d (date | datetime): The date or datetime object to format.
        fmt (str, optional): The desired output format string.
            Defaults to DEFAULT_DATE_FORMAT ("%Y-%m-%d").

    Returns:
        str: The formatted date string.

    Raises:
        TypeError: If the provided argument is not a date or datetime object.
    """
    if isinstance(d, (datetime, date)):
        return d.strftime(fmt)
    raise TypeError("Expected a date or datetime object.")


def parse_date(date_str: str, fmt: str = DEFAULT_DATE_FORMAT) -> date:
    """
    Parse a string into a date object using the given format.

    Args:
        date_str (str): The date string to parse.
        fmt (str, optional): The expected date format.
            Defaults to DEFAULT_DATE_FORMAT ("%Y-%m-%d").

    Returns:
        date: A datetime.date object parsed from the string.

    Raises:
        ValueError: If parsing fails due to invalid string or format mismatch.
    """
    try:
        return datetime.strptime(date_str, fmt).date()
    except Exception as e:
        logger.error(f"❌ Failed to parse date '{date_str}' using format '{fmt}': {e}")
        raise


# ====================================================================================================
# 5. WEEK HELPERS
# ----------------------------------------------------------------------------------------------------
def get_start_of_week(ref_date: date | None = None) -> date:
    """
    Return the Monday (start of week) for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        date: The Monday of the same week as ref_date.
    """
    if ref_date is None:
        ref_date = date.today()
    return ref_date - timedelta(days=ref_date.weekday())


def get_end_of_week(ref_date: date | None = None) -> date:
    """
    Return the Sunday (end of week) for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        date: The Sunday of the same week as ref_date.
    """
    return get_start_of_week(ref_date) + timedelta(days=6)


def get_week_range(ref_date: date | None = None) -> Tuple[date, date]:
    """
    Return both the Monday (start) and Sunday (end) of the week for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        Tuple[date, date]: A tuple containing (start_of_week, end_of_week).
    """
    start = get_start_of_week(ref_date)
    end = start + timedelta(days=6)
    return (start, end)


# ====================================================================================================
# 6. MONTH HELPERS
# ----------------------------------------------------------------------------------------------------
def get_start_of_month(ref_date: date | None = None) -> date:
    """
    Return the first day of the month for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        date: The first day of the month containing ref_date.
    """
    if ref_date is None:
        ref_date = date.today()
    return ref_date.replace(day=1)


def get_end_of_month(ref_date: date | None = None) -> date:
    """
    Return the last day of the month for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        date: The last day of the month containing ref_date.
    """
    if ref_date is None:
        ref_date = date.today()
    _, last_day = calendar.monthrange(ref_date.year, ref_date.month)
    return ref_date.replace(day=last_day)


def get_month_range(year: int, month: int) -> Tuple[date, date]:
    """
    Return the first and last day of a specified month.

    Args:
        year (int): The target year.
        month (int): The target month (1–12).

    Returns:
        Tuple[date, date]: A tuple containing (first_day, last_day) for that month.
    """
    first = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    return (first, date(year, month, last_day))


# ====================================================================================================
# 7. DATE RANGE UTILITIES
# ----------------------------------------------------------------------------------------------------
def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of consecutive dates between two given dates (inclusive).

    Args:
        start_date (date): The start date.
        end_date (date): The end date.

    Returns:
        List[date]: List of all dates between start_date and end_date (inclusive).

    Raises:
        ValueError: If start_date occurs after end_date.
    """
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date.")
    delta = (end_date - start_date).days
    return [start_date + timedelta(days=i) for i in range(delta + 1)]


def is_within_range(check_date: date, start_date: date, end_date: date) -> bool:
    """
    Check if a given date falls within a specified inclusive date range.

    Args:
        check_date (date): Date to check.
        start_date (date): Start of range.
        end_date (date): End of range.

    Returns:
        bool: True if check_date lies between start_date and end_date (inclusive).
    """
    return start_date <= check_date <= end_date


# ====================================================================================================
# 8. REPORTING HELPERS
# ----------------------------------------------------------------------------------------------------
def get_fiscal_quarter(ref_date: date | None = None) -> str:
    """
    Return the fiscal quarter label (Q1–Q4) for a given date.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        str: Fiscal quarter label formatted as "QX YYYY".
    """
    if ref_date is None:
        ref_date = date.today()
    q = (ref_date.month - 1) // 3 + 1
    return f"Q{q} {ref_date.year}"


def get_week_id(ref_date: date | None = None) -> str:
    """
    Return a standardised ISO week identifier in 'YYYY-WW' format.

    Args:
        ref_date (date | None, optional): The reference date.
            Defaults to today's date.

    Returns:
        str: ISO week label (e.g. '2025-W45').
    """
    if ref_date is None:
        ref_date = date.today()
    iso_year, iso_week, _ = ref_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


# ====================================================================================================
# 9. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone test to verify correct functionality and formatting
    of all date/time helper utilities.
    """
    logger.info("🕒 Running C07_datetime_utils self-test...")

    today = get_today()
    logger.info(f"Today's date: {as_str(today)}")
    logger.info(f"Now: {as_str(get_now())}")
    logger.info(f"Timestamp: {timestamp_now()}")
    logger.info(f"Start of week: {as_str(get_start_of_week(today))}")
    logger.info(f"End of week: {as_str(get_end_of_week(today))}")

    start, end = get_week_range(today)
    logger.info(f"Week range: ({as_str(start)}, {as_str(end)})")

    logger.info(f"Start of month: {as_str(get_start_of_month(today))}")
    logger.info(f"End of month: {as_str(get_end_of_month(today))}")

    m_start, m_end = get_month_range(2025, 10)
    logger.info(f"Month range (2025-10): ({as_str(m_start)}, {as_str(m_end)})")

    logger.info(f"Fiscal quarter: {get_fiscal_quarter(today)}")
    logger.info(f"Week ID: {get_week_id(today)}")

    dr = generate_date_range(start, end)
    logger.info(f"Generated {len(dr)} days this week: {[as_str(d) for d in dr]}")

    logger.info(f"Is {as_str(today)} within this week? {is_within_range(today, start, end)}")
    logger.info("✅ Date utilities test complete.")
