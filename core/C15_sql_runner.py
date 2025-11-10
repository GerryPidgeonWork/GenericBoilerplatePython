# ====================================================================================================
# C15_sql_runner.py
# ----------------------------------------------------------------------------------------------------
# Provides a safe and convenient interface to execute .sql files stored in the /sql/ directory.
#
# Purpose:
#   - Allow projects to keep all SQL logic external (in /sql/ files) while running them easily in Python.
#   - Support lightweight parameter substitution for dynamic filters (e.g. {start_date}, {end_date}).
#   - Integrate seamlessly with the Snowflake connector (C14_snowflake_connector) and central logger.
#
# Usage:
#   from core.C15_sql_runner import run_sql_file
#
#   conn = connect_to_snowflake("user@gopuff.com")
#   result = run_sql_file(conn, "orders_summary.sql", params={"start_date": "2025-11-01"})
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
from core.C14_snowflake_connector import run_query               # Reuse the SQL executor

# ====================================================================================================
# 3. LOAD AND EXECUTE SQL FILE
# ----------------------------------------------------------------------------------------------------
def load_sql_file(file_name: str, params: dict | None = None) -> str:
    """
    Load and optionally format a SQL file from the /sql/ directory.

    Args:
        file_name (str):
            The name of the SQL file (with or without '.sql' extension).
            e.g. "monthly_report.sql" or "queries/monthly_report.sql"
        params (dict | None, optional):
            Optional dictionary of parameters for string substitution.
            Example: {"start_date": "2025-11-01", "end_date": "2025-11-30"}

    Returns:
        str: The formatted SQL string ready for execution.

    Raises:
        FileNotFoundError: If the specified SQL file cannot be found.
        ValueError: If formatting fails due to missing parameters.
    """
    sql_folder = Path(__file__).resolve().parent.parent / "sql"
    sql_path = (sql_folder / file_name).with_suffix(".sql")

    if not sql_path.exists():
        logger.error(f"❌ SQL file not found: {sql_path}")
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8")

    if params:
        try:
            sql_text = sql_text.format(**params)
            logger.info(f"🧩 Applied SQL parameters: {params}")
        except KeyError as e:
            logger.error(f"❌ Missing parameter in SQL template: {e}")
            raise ValueError(f"Missing parameter for SQL substitution: {e}")

    logger.info(f"📄 Loaded SQL file: {sql_path.name}")
    return sql_text


def run_sql_file(conn, file_name: str, params: dict | None = None, fetch: bool = True):
    """
    Load and execute a SQL file via an active Snowflake connection.

    Args:
        conn (snowflake.connector.connection.SnowflakeConnection):
            Active Snowflake connection object.
        file_name (str):
            The name of the SQL file (e.g., 'daily_orders.sql').
        params (dict | None, optional):
            Optional parameters to inject into the SQL file.
        fetch (bool, optional):
            Whether to fetch results. Defaults to True.

    Returns:
        list[tuple] | None: Query results if fetch=True, otherwise None.
    """
    try:
        sql_text = load_sql_file(file_name, params)
        logger.info(f"🚀 Executing SQL file: {file_name}")
        return run_query(conn, sql_text, fetch=fetch)
    except Exception as e:
        log_exception(e, context=f"Running SQL file: {file_name}")
        return None


# ====================================================================================================
# 4. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone test to verify SQL loading, parameter substitution, and execution.
    Expects an active Snowflake environment and a sample .sql file in /sql/.
    """
    from core.C14_snowflake_connector import connect_to_snowflake

    print("🔍 Running C15_sql_runner self-test...")

    try:
        test_email = input("Enter your Gopuff email: ").strip()
        conn = connect_to_snowflake(test_email)
        if not conn:
            print("❌ Could not connect to Snowflake.")
            sys.exit(1)

        # --- Create a temporary SQL file for demonstration ---
        sql_dir = Path(__file__).resolve().parent.parent / "sql"
        sql_dir.mkdir(exist_ok=True)
        sample_sql = sql_dir / "test_query.sql"
        sample_sql.write_text("SELECT CURRENT_USER() AS user, CURRENT_DATE() AS today, '{start_date}' AS start_date;", encoding="utf-8")

        # --- Execute using parameter substitution ---
        params = {"start_date": "2025-11-01"}
        result = run_sql_file(conn, "test_query.sql", params=params)

        if result:
            logger.info(f"🧾 SQL Runner Output: {result}")
            print(result)

        conn.close()
        logger.info("✅ SQL runner test completed successfully.")
    except KeyboardInterrupt:
        print("\n🛑 Test aborted by user.")
    except Exception as e:
        log_exception(e, context="C15_sql_runner self-test")
