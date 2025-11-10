# ====================================================================================================
# C19_api_manager.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable REST API utilities for authenticated and unauthenticated requests.
#
# Purpose:
#   - Standardise GET/POST/PUT/DELETE requests using the requests library.
#   - Handle JSON parsing, retries, and error logging automatically.
#   - Provide consistent interfaces for API-based integrations.
#
# Notes:
#   - All external packages (e.g., requests) are imported centrally via C00_set_packages.py.
#   - Use with non-Google APIs (Google Drive handled separately via P09_gdrive_api.py).
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
# 3. API REQUEST FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def api_request(
    method: str,
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    data: dict | None = None,
    json_data: dict | None = None,
    retries: int = 3,
    timeout: int = 15,
):
    """
    Executes an HTTP API request with retry and logging support.

    Args:
        method (str):
            HTTP method ('GET', 'POST', 'PUT', 'DELETE').
        url (str):
            The API endpoint URL.
        headers (dict | None):
            Optional dictionary of HTTP headers.
        params (dict | None):
            URL parameters for GET requests.
        data (dict | None):
            Form data for POST/PUT requests.
        json_data (dict | None):
            JSON body for POST/PUT requests.
        retries (int):
            Number of retry attempts on failure.
        timeout (int):
            Maximum time (seconds) to wait for a response.

    Returns:
        requests.Response | None:
            The response object if successful, otherwise None.
    """
    method = method.upper().strip()
    attempt = 0

    while attempt < retries:
        attempt += 1
        try:
            logger.info(f"🌐 [{method}] Attempt {attempt}/{retries}: {url}")
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout,
            )

            if response.ok:
                logger.info(f"✅ [{response.status_code}] Successful request to {url}")
                return response
            else:
                logger.warning(
                    f"⚠️  [{response.status_code}] API request failed: {response.text[:250]}"
                )

        except requests.Timeout:
            logger.warning(f"⏰ Timeout on attempt {attempt}/{retries} for {url}")
        except requests.ConnectionError as e:
            logger.error(f"🔌 Connection error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error during API call: {e}")

        if attempt < retries:
            time.sleep(2)

    logger.error(f"❌ Failed to complete request after {retries} attempts: {url}")
    return None


# ====================================================================================================
# 4. HELPER FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def get_json(url: str, headers: dict | None = None, params: dict | None = None) -> dict | None:
    """
    Convenience function to perform a GET request and return parsed JSON data.

    Args:
        url (str):
            The API endpoint URL.
        headers (dict | None):
            Optional HTTP headers.
        params (dict | None):
            Optional query parameters.

    Returns:
        dict | None:
            Parsed JSON dictionary if successful, otherwise None.
    """
    response = api_request("GET", url, headers=headers, params=params)
    if response is None:
        return None
    try:
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse JSON from {url}: {e}")
        return None


def post_json(url: str, json_data: dict, headers: dict | None = None) -> dict | None:
    """
    Sends a POST request with JSON payload and returns parsed JSON response.

    Args:
        url (str):
            The API endpoint URL.
        json_data (dict):
            The JSON payload to send.
        headers (dict | None):
            Optional HTTP headers.

    Returns:
        dict | None:
            Parsed JSON response if successful, otherwise None.
    """
    response = api_request("POST", url, headers=headers, json_data=json_data)
    if response is None:
        return None
    try:
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse JSON from POST response: {e}")
        return None


def get_auth_header(token: str, bearer: bool = True) -> dict:
    """
    Builds a standardised Authorization header.

    Args:
        token (str):
            API token or key.
        bearer (bool):
            Whether to prefix with 'Bearer' (default = True).

    Returns:
        dict:
            HTTP headers including Authorization.
    """
    if bearer:
        return {"Authorization": f"Bearer {token}"}
    return {"Authorization": token}


# ====================================================================================================
# 5. SELF TEST
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Runs a simple self-test by calling a public test API (https://api.github.com)
    to verify connectivity and JSON response handling.
    """
    logger.info("🔍 Running C18_api_manager self-test...")

    test_url = "https://api.github.com"
    result = get_json(test_url)

    if result:
        logger.info(f"✅ API Self-test successful. Keys returned: {list(result.keys())[:5]}")
    else:
        logger.error("❌ API Self-test failed.")

    logger.info("✅ C18_api_manager self-test complete.")
