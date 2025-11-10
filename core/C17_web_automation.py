# ====================================================================================================
# C17_selenium_utils.py
# ----------------------------------------------------------------------------------------------------
# Provides standardised Selenium utilities for browser automation across projects.
#
# Purpose:
#   - Simplify Selenium setup with Chrome WebDriver.
#   - Handle dynamic driver paths and profile loading.
#   - Provide utility functions for scrolling, waiting, and element interaction.
#
# Notes:
#   - All Selenium packages are imported centrally via C00_set_packages.py.
#   - Automatically detects Chrome installation and driver compatibility.
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
from core.C02_system_processes import detect_os


# ====================================================================================================
# 3. SELENIUM SETUP FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def get_chrome_driver(profile_name: str | None = None, headless: bool = False):
    """
    Creates and returns a configured Selenium Chrome WebDriver instance.

    Args:
        profile_name (str | None):
            Name of the Chrome profile to use (e.g. 'Default', 'Profile 2').
            If None, a temporary session will be started.
        headless (bool):
            Whether to run Chrome in headless mode (without UI).

    Returns:
        webdriver.Chrome | None:
            Configured Selenium driver instance if successful, otherwise None.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")

        if headless:
            options.add_argument("--headless=new")

        os_type = detect_os().lower()
        if "windows" in os_type:
            base_path = Path.home() / "AppData/Local/Google/Chrome/User Data"
        elif "mac" in os_type:
            base_path = Path.home() / "Library/Application Support/Google/Chrome"
        else:
            base_path = Path.home() / ".config/google-chrome"

        if profile_name:
            options.add_argument(f"--user-data-dir={base_path}")
            options.add_argument(f"--profile-directory={profile_name}")
            logger.info(f"🧠 Loaded Chrome profile: {profile_name}")

        driver = webdriver.Chrome(options=options)
        logger.info("✅ Chrome WebDriver initialised successfully.")
        return driver

    except Exception as e:
        logger.error(f"❌ Failed to initialise Chrome WebDriver: {e}")
        return None


# ====================================================================================================
# 4. SELENIUM HELPER FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def wait_for_element(driver, by: str, selector: str, timeout: int = 10):
    """
    Waits for a specific element to become visible on the page.

    Args:
        driver (webdriver.Chrome):
            Active Selenium driver instance.
        by (str):
            Locator strategy (e.g., 'xpath', 'css selector', 'id').
        selector (str):
            The selector string to match the target element.
        timeout (int):
            Maximum wait time in seconds (default = 10).

    Returns:
        selenium.webdriver.remote.webelement.WebElement | None:
            The located element if found within the timeout, otherwise None.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((getattr(By, by.upper()), selector))
        )
        logger.info(f"✅ Element located by {by}: {selector}")
        return element
    except Exception as e:
        logger.warning(f"⚠️  Element not found by {by}: {selector} ({e})")
        return None


def scroll_to_bottom(driver, pause_time: float = 1.0):
    """
    Scrolls gradually to the bottom of the web page, allowing for lazy-loaded content.

    Args:
        driver (webdriver.Chrome):
            Active Selenium driver instance.
        pause_time (float):
            Delay in seconds between each scroll action (default = 1.0).

    Returns:
        None
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    logger.info("📜 Finished scrolling to bottom of the page.")


def click_element(driver, by: str, selector: str):
    """
    Safely clicks an element located by the specified selector.

    Args:
        driver (webdriver.Chrome):
            Active Selenium driver instance.
        by (str):
            Locator strategy (e.g., 'xpath', 'css selector', 'id').
        selector (str):
            The selector string to match the target element.

    Returns:
        bool:
            True if the click was successful, False otherwise.
    """
    element = wait_for_element(driver, by, selector)
    if not element:
        logger.warning(f"⚠️  Element not clickable (not found): {selector}")
        return False
    try:
        element.click()
        logger.info(f"🖱️  Clicked element: {selector}")
        return True
    except Exception as e:
        logger.error(f"❌ Error clicking element: {e}")
        return False


def close_driver(driver):
    """
    Closes the active Selenium WebDriver session.

    Args:
        driver (webdriver.Chrome):
            Active WebDriver instance to close.

    Returns:
        None
    """
    try:
        driver.quit()
        logger.info("🧹 Selenium driver session closed cleanly.")
    except Exception as e:
        logger.error(f"❌ Error closing driver: {e}")


# ====================================================================================================
# 5. SELF TEST
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Self-test for verifying Selenium driver setup and core helper functions.
    Opens Google, waits for the search box, scrolls, and closes the session.
    """
    logger.info("🔍 Running C17_selenium_utils self-test...")

    driver = get_chrome_driver(profile_name=None, headless=True)
    if driver:
        try:
            driver.get("https://www.google.com")
            wait_for_element(driver, "name", "q", 5)
            scroll_to_bottom(driver, 0.5)
        finally:
            close_driver(driver)
            logger.info("✅ Selenium self-test completed successfully.")
    else:
        logger.error("❌ Selenium self-test failed: WebDriver not created.")
