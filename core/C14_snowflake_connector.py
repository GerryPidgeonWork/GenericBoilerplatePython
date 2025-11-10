# ====================================================================================================
# C14_snowflake_connector.py
# ----------------------------------------------------------------------------------------------------
# Provides a unified Snowflake connection interface for GenericBoilerplatePython projects.
#
# Purpose:
#   - Establish secure Okta SSO connections to Snowflake.
#   - Auto-select the most appropriate Role/Warehouse context.
#   - Support both interactive (CLI/GUI) and automated (config-based) connections.
#
# Features:
#   • Pre-configured for Gopuff's Snowflake Okta setup (non-secret).
#   • Accepts user email (validated against domain).
#   • Auto-applies best matching context from priority list.
#   • Logs all steps and exceptions centrally via C03_logging_handler.
#   • Includes run_query() helper for convenient SQL execution.
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
from C04_config_loader import get_config


# ====================================================================================================
# 3. DEFAULT SNOWFLAKE CONFIGURATION
# ----------------------------------------------------------------------------------------------------
SNOWFLAKE_ACCOUNT = "HC77929-GOPUFF"
SNOWFLAKE_EMAIL_DOMAIN = "gopuff.com"

CONTEXT_PRIORITY = [
    {"role": "OKTA_ANALYTICS_ROLE", "warehouse": "ANALYTICS"},
    {"role": "OKTA_READER_ROLE",    "warehouse": "READER_WH"},
]

DEFAULT_DATABASE = "DBT_PROD"
DEFAULT_SCHEMA = "CORE"
AUTHENTICATOR = "externalbrowser"
TIMEOUT_SECONDS = 20


# ====================================================================================================
# 4. SNOWFLAKE CREDENTIALS BUILDER
# ----------------------------------------------------------------------------------------------------
def get_snowflake_credentials(email_address: str) -> dict | None:
    """
    Validate user email and build credentials for Okta-based Snowflake login.

    Args:
        email_address (str): User's full email (must match company domain).

    Returns:
        dict | None: Connection credentials dictionary, or None if invalid.
    """
    if not email_address or "@" not in email_address:
        logger.error(f"❌ Invalid email provided: '{email_address}'")
        return None

    if not email_address.endswith(f"@{SNOWFLAKE_EMAIL_DOMAIN}"):
        logger.error(f"❌ Email '{email_address}' does not match domain '{SNOWFLAKE_EMAIL_DOMAIN}'")
        return None

    os.environ["SNOWFLAKE_USER"] = email_address
    logger.info(f"📧 Using Snowflake email: {email_address}")

    return {
        "user": email_address,
        "account": SNOWFLAKE_ACCOUNT,
        "authenticator": AUTHENTICATOR,
    }


# ====================================================================================================
# 5. SNOWFLAKE CONTEXT SETTER
# ----------------------------------------------------------------------------------------------------
def set_snowflake_context(conn, role: str, warehouse: str,
                          database: str = DEFAULT_DATABASE,
                          schema: str = DEFAULT_SCHEMA) -> bool:
    """
    Set active Snowflake session context (role, warehouse, database, schema).

    Args:
        conn: Active Snowflake connection.
        role (str): Role name to apply.
        warehouse (str): Warehouse name to use.
        database (str, optional): Database name. Defaults to DEFAULT_DATABASE.
        schema (str, optional): Schema name. Defaults to DEFAULT_SCHEMA.

    Returns:
        bool: True on success, False on failure.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"USE ROLE {role}")
        cur.execute(f"USE WAREHOUSE {warehouse}")
        cur.execute(f"USE DATABASE {database}")
        cur.execute(f"USE SCHEMA {schema}")

        cur.execute("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        r, wh, db, sc = cur.fetchone()
        logger.info(f"📂 Active Context: Role={r}, Warehouse={wh}, Database={db}, Schema={sc}")
        cur.close()
        return True
    except Exception as e:
        log_exception(e, context=f"Setting context {role}/{warehouse}")
        cur.close()
        return False


# ====================================================================================================
# 6. SNOWFLAKE CONNECTION HANDLER
# ----------------------------------------------------------------------------------------------------
def connect_to_snowflake(email_address: str):
    """
    Connect to Snowflake via Okta SSO and automatically set the best available context.

    Args:
        email_address (str): Full email (must match company domain).

    Returns:
        snowflake.connector.connection.SnowflakeConnection | None
    """
    creds = get_snowflake_credentials(email_address)
    if not creds:
        return None

    logger.info("🔄 Starting Snowflake SSO connection via Okta...")
    print("Please complete the Okta authentication in your browser window.\n")

    conn_container = {}

    def connect_thread():
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                conn = snowflake.connector.connect(**creds)
                conn_container["conn"] = conn
        except Exception as e:
            conn_container["error"] = e

    thread = threading.Thread(target=connect_thread, daemon=True)
    thread.start()
    thread.join(timeout=TIMEOUT_SECONDS)

    if thread.is_alive():
        logger.error(f"⏰ Timeout after {TIMEOUT_SECONDS} seconds waiting for Okta login.")
        return None

    if "error" in conn_container:
        err = str(conn_container["error"])
        logger.error(f"❌ Connection failed: {err}")
        if "differs from the user currently logged in" in err:
            logger.warning("User mismatch — try logging out of other Okta sessions.")
            os.environ.pop("SNOWFLAKE_USER", None)
        return None

    if "conn" not in conn_container:
        logger.error("❌ Unknown connection error — no connection object returned.")
        return None

    conn = conn_container["conn"]
    logger.info(f"✅ Connected successfully as {creds['user']}")
    print("Retrieving available roles and warehouses...")

    try:
        cur = conn.cursor()
        available_roles = {row[1] for row in cur.execute("SHOW ROLES")}
        available_whs = {row[0] for row in cur.execute("SHOW WAREHOUSES")}
        cur.close()
    except Exception as e:
        log_exception(e, context="Retrieving roles/warehouses")
        conn.close()
        return None

    for context in CONTEXT_PRIORITY:
        role = context["role"]
        wh = context["warehouse"]
        if role in available_roles and wh in available_whs:
            logger.info(f"✅ Found matching context: {role}/{wh}")
            if set_snowflake_context(conn, role, wh):
                return conn
            logger.warning(f"⚠️ Failed to apply context {role}/{wh}. Trying next...")
        else:
            logger.debug(f"Context not available: {role}/{wh}")

    logger.error("❌ No valid role/warehouse context found.")
    print("Ensure access to one of the following pairs:")
    for c in CONTEXT_PRIORITY:
        print(f"  - {c['role']} / {c['warehouse']}")
    conn.close()
    return None


# ====================================================================================================
# 7. QUERY EXECUTION HELPER
# ----------------------------------------------------------------------------------------------------
def run_query(conn, sql: str, fetch: bool = True):
    """
    Execute a Snowflake SQL query with automatic logging and error handling.

    Args:
        conn: Active Snowflake connection.
        sql (str): SQL query to execute.
        fetch (bool, optional): If True, fetch and return results. Defaults to True.

    Returns:
        list[tuple] | None: Query results if fetch=True, otherwise None.
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        preview = sql.replace("\n", " ")[:100]
        logger.info(f"🧠 Executed SQL: {preview}{'...' if len(sql) > 100 else ''}")
        if fetch:
            data = cur.fetchall()
            cur.close()
            logger.info(f"📦 Rows fetched: {len(data)}")
            return data
        cur.close()
        logger.info("✅ Query executed successfully (no fetch).")
        return None
    except Exception as e:
        log_exception(e, context=f"Running query: {sql[:80]}")
        return None


# ====================================================================================================
# 8. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Manual test runner for verifying Snowflake SSO and auto-context setup.
    """
    print("🔍 Running C14_snowflake_connector self-test...")

    test_email = get_config("snowflake", "email", default="")
    if not test_email:
        test_email = input("Enter your Gopuff email: ").strip()

    conn = connect_to_snowflake(test_email)
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_ROLE(),
                   CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
        """)
        user, acct, role, wh, db, sc = cur.fetchone()
        print(f"\n👤 {user} | 🏢 {acct} | 🧩 {role} | 🏭 {wh} | 📚 {db} | 📁 {sc}\n")
        cur.close()

        # --- Test the query helper ---
        sample_sql = "SELECT CURRENT_DATE(), CURRENT_TIMESTAMP();"
        result = run_query(conn, sample_sql)
        if result:
            print(f"🧾 Sample query result: {result}")

        conn.close()
        logger.info("✅ Connection closed cleanly.")
    else:
        logger.error("❌ Test failed: Connection not established.")
