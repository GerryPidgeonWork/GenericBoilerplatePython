# ====================================================================================================
# C16_cache_manager.py
# ----------------------------------------------------------------------------------------------------
# Provides a lightweight caching framework for temporary or reusable data.
#
# Purpose:
#   - Store and retrieve frequently used data (e.g., API responses, DataFrames, query results).
#   - Improve performance by avoiding repeated expensive operations.
#   - Ensure consistent cache directory handling across all projects.
#
# Supported Formats:
#   - JSON for dictionary-like data.
#   - CSV for DataFrames.
#   - Pickle for arbitrary Python objects.
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
from core.C07_datetime_utils import as_str, get_today

# ====================================================================================================
# 3. GLOBAL SETTINGS
# ----------------------------------------------------------------------------------------------------
CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ====================================================================================================
# 4. CORE CACHE FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def get_cache_path(name: str, fmt: str = "json") -> Path:
    """
    Build the full path to a cache file.

    Args:
        name (str):
            Logical name for the cache file (e.g., "orders_today").
        fmt (str, optional):
            File format for the cache. Options:
            - "json" : JSON object
            - "csv"  : DataFrame
            - "pkl"  : Pickle object

    Returns:
        Path: Full filesystem path of the cache file.
    """
    extension_map = {"json": ".json", "csv": ".csv", "pkl": ".pkl"}
    ext = extension_map.get(fmt.lower(), ".json")
    return CACHE_DIR / f"{name}{ext}"


def save_cache(name: str, data, fmt: str = "json") -> Path | None:
    """
    Save data to a cache file in the specified format.

    Args:
        name (str):
            Name of the cache file without extension.
        data (Any):
            The data or object to save.
        fmt (str, optional):
            Format for saving the cache. Default = "json".
            Options: "json", "csv", "pkl".

    Returns:
        Path | None:
            Path to the saved cache file if successful, otherwise None.

    Raises:
        ValueError:
            If the format is unsupported or data type does not match.
    """
    path = get_cache_path(name, fmt)
    try:
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        elif fmt == "csv" and isinstance(data, pd.DataFrame):
            data.to_csv(path, index=False)
        elif fmt == "pkl":
            with open(path, "wb") as f:
                pickle.dump(data, f)
        else:
            raise ValueError(f"Unsupported format '{fmt}' or invalid data type.")
        logger.info(f"💾 Cache saved: {path.name}")
        return path
    except Exception as e:
        logger.error(f"❌ Failed to save cache '{name}': {e}")
        return None


def load_cache(name: str, fmt: str = "json"):
    """
    Load cached data if it exists.

    Args:
        name (str):
            Name of the cache file without extension.
        fmt (str, optional):
            Cache file format. Default = "json".

    Returns:
        Any:
            The loaded cached data (dict, DataFrame, object, etc.), or None if not found.
    """
    path = get_cache_path(name, fmt)
    if not path.exists():
        logger.warning(f"⚠️  Cache not found: {path.name}")
        return None

    try:
        if fmt == "json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif fmt == "csv":
            data = pd.read_csv(path)
        elif fmt == "pkl":
            with open(path, "rb") as f:
                data = pickle.load(f)
        else:
            raise ValueError(f"Unsupported format '{fmt}'.")
        logger.info(f"✅ Cache loaded: {path.name}")
        return data
    except Exception as e:
        logger.error(f"❌ Error loading cache '{name}': {e}")
        return None


def clear_cache(name: str | None = None):
    """
    Delete one or all cache files.

    Args:
        name (str | None):
            - If provided: deletes specific cache file (any format).
            - If None: deletes all cache files in the cache directory.

    Returns:
        None
    """
    if name:
        deleted = False
        for ext in ["json", "csv", "pkl"]:
            path = get_cache_path(name, ext)
            if path.exists():
                path.unlink()
                logger.info(f"🗑️  Deleted cache: {path.name}")
                deleted = True
        if not deleted:
            logger.warning(f"⚠️  No cache found for '{name}'.")
    else:
        count = len(list(CACHE_DIR.glob("*")))
        for f in CACHE_DIR.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass
        logger.info(f"🧹 Cleared {count} cache file(s) from {CACHE_DIR}.")


def list_cache_files() -> list[Path]:
    """
    List all current cache files in the cache directory.

    Returns:
        list[Path]: List of cache file paths currently present.
    """
    files = list(CACHE_DIR.glob("*"))
    logger.info(f"📦 Found {len(files)} cached file(s).")
    return files


# ====================================================================================================
# 5. SELF TEST
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Self-test to verify caching system works as expected.
    Creates, loads, lists, and clears example cache files.
    """
    logger.info("🔍 Running C16_cache_manager self-test...")

    sample_data = {"user": "gerry", "date": as_str(get_today()), "value": 123}
    df = pd.DataFrame([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])

    # Save test caches
    save_cache("test_json", sample_data, "json")
    save_cache("test_csv", df, "csv")
    save_cache("test_pickle", df, "pkl")

    # Load test caches
    load_cache("test_json", "json")
    load_cache("test_csv", "csv")
    load_cache("test_pickle", "pkl")

    # List all cache files
    list_cache_files()

    # Clear test caches
    clear_cache("test_json")
    clear_cache("test_csv")
    clear_cache("test_pickle")

    logger.info("✅ C16_cache_manager self-test complete.")
