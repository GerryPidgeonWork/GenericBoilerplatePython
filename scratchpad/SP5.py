# ====================================================================================================
# SP5.py
# ----------------------------------------------------------------------------------------------------
# Scratchpad / Experimental Script
#
# Purpose:
#   - Used for quick testing, prototyping, and validating snippets of logic.
#   - Can safely import and use any functions or modules from the core framework.
#   - Should not contain production code — migrate validated snippets into implementation/ or core/.
#
# Usage:
#   - Run interactively to test logic:   python scratchpad/SP1.py
#   - Use imports from core for consistency:
#         from core.C01_set_file_paths import DATA_DIR
#         from core.C03_logging_handler import get_logger
#
# Notes:
#   - Scratchpad files are excluded from version control if they contain sensitive or temporary code.
#   - You can create SP2.py, SP3.py, etc. for separate experiments.
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # Add project root so /core/ is importable from anywhere
sys.dont_write_bytecode = True                                   # Prevent creation of __pycache__ folders


# ====================================================================================================
# 2. PROJECT IMPORTS
# ----------------------------------------------------------------------------------------------------
# Bring in standard libraries and settings from the central import hub.
# (Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.)
# ====================================================================================================
from core.C00_set_packages import *                              # Imports all universal packages


# ====================================================================================================
# 3. SCRATCHPAD
# ----------------------------------------------------------------------------------------------------
# Script for writing and testing code
# ====================================================================================================
