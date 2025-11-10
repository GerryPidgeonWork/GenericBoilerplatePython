# ====================================================================================================
# C04_config_loader.py
# ----------------------------------------------------------------------------------------------------
# Centralised configuration and environment loader for all GenericBoilerplatePython projects.
#
# Purpose:
#   - Automatically detect and load configuration files from the /config/ directory.
#   - Merge data from .env, .yaml, and .json files into a unified CONFIG dictionary.
#   - Provide helper functions for safe key retrieval and dynamic reloads.
#   - Log all load activity using the central logging handler.
#
# Usage:
#   from core.C04_config_loader import CONFIG, get_config
#   print(CONFIG["snowflake"]["user"])
#   api_key = get_config("google", "api_key")
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


# ====================================================================================================
# 3. CONFIGURATION LOADER
# ----------------------------------------------------------------------------------------------------
# Detects and loads supported configuration files (.env, .yaml, .json)
# into a unified CONFIG dictionary for global use.
# ====================================================================================================

logger = get_logger(__name__)

# --- Global configuration dictionary ---
CONFIG: Dict[str, Any] = {}

# --- Supported config file names ---
DEFAULT_FILES = {
    "env": ".env",
    "yaml": ["config.yaml", "config.yml"],
    "json": "settings.json"
}


def load_env_file(env_path: Path) -> None:
    """
    Load environment variables from a .env file into os.environ.

    Args:
        env_path (Path): Path to the .env file.
    """
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
        logger.info(f"✅ Loaded environment variables from {env_path.name}")
    else:
        logger.warning("⚠️  No .env file found in /config/")


def load_yaml_config(yaml_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        yaml_path (Path): Path to the YAML configuration file.

    Returns:
        Dict[str, Any]: Parsed YAML content as a Python dictionary.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        logger.info(f"✅ Loaded YAML configuration: {yaml_path.name}")
        return data
    except Exception as e:
        log_exception(e, context=f"Loading YAML config ({yaml_path})")
        return {}


def load_json_config(json_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        json_path (Path): Path to the JSON configuration file.

    Returns:
        Dict[str, Any]: Parsed JSON content as a Python dictionary.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.info(f"✅ Loaded JSON configuration: {json_path.name}")
        return data
    except Exception as e:
        log_exception(e, context=f"Loading JSON config ({json_path})")
        return {}


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries recursively (override values take precedence).

    Args:
        base (Dict[str, Any]): Base configuration dictionary.
        override (Dict[str, Any]): Overrides to apply.

    Returns:
        Dict[str, Any]: Merged configuration dictionary.
    """
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = merge_dicts(base[key], value)
        else:
            base[key] = value
    return base


def initialise_config() -> Dict[str, Any]:
    """
    Detect and load configuration files into a unified CONFIG dictionary.

    Returns:
        Dict[str, Any]: Merged configuration data.
    """
    global CONFIG
    CONFIG = {}

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # --- 1. Load .env ---
        env_path = CONFIG_DIR / DEFAULT_FILES["env"]
        load_env_file(env_path)

        # --- 2. Load YAML (config.yaml or config.yml) ---
        for yaml_file in DEFAULT_FILES["yaml"]:
            yaml_path = CONFIG_DIR / yaml_file
            if yaml_path.exists():
                CONFIG = merge_dicts(CONFIG, load_yaml_config(yaml_path))

        # --- 3. Load JSON (settings.json) ---
        json_path = CONFIG_DIR / DEFAULT_FILES["json"]
        if json_path.exists():
            CONFIG = merge_dicts(CONFIG, load_json_config(json_path))

        logger.info("✅ Configuration initialised successfully.")
        return CONFIG

    except Exception as e:
        log_exception(e, context="Initialising configuration")
        return CONFIG


def get_config(section: str, key: str, default: Any = None) -> Any:
    """
    Retrieve a specific configuration value safely.

    Args:
        section (str): Top-level configuration key (e.g., "snowflake").
        key (str): Nested key within the section (e.g., "user").
        default (Any, optional): Default value if key is not found.

    Returns:
        Any: The retrieved configuration value or default.
    """
    try:
        return CONFIG.get(section, {}).get(key, default)
    except Exception:
        return default


def reload_config() -> Dict[str, Any]:
    """
    Reload configuration files and return the updated CONFIG dictionary.

    Returns:
        Dict[str, Any]: Updated configuration dictionary.
    """
    logger.info("🔄 Reloading configuration files...")
    return initialise_config()


# --- Initialise immediately when imported ---
CONFIG = initialise_config()


# ====================================================================================================
# 4. MAIN EXECUTION (STANDALONE TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone execution test.
    Prints loaded configuration summary and verifies file detection.
    """
    print("🔍 CONFIGURATION TEST STARTED")
    print(f"Config directory: {CONFIG_DIR}")
    print(f"Loaded keys: {list(CONFIG.keys()) if CONFIG else 'No config found'}")
    print(f"Example lookup: {get_config('snowflake', 'user', '<not set>')}")
    print("✅ Test complete.")
