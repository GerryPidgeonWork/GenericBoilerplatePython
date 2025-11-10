# ====================================================================================================
# C00_set_packages.py
# ----------------------------------------------------------------------------------------------------
# Centralises all package imports for the project.
#
# Purpose:
#   - Provide a single file to manage all external and standard library imports.
#   - Simplify other modules, which can just import * from this file.
#   - List all project dependencies in one place.
#
# Usage:
#   from core.C00_set_packages import *
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


# ====================================================================================================
# 3. STANDARD LIBRARY IMPORTS
# ----------------------------------------------------------------------------------------------------
# Import common Python standard libraries used across the project.
# Keep this section limited to modules that are guaranteed to exist in every Python installation.
# ====================================================================================================
import os                                                                               # OS-level operations (file paths, environment variables)
import io                                                                               # Core I/O streams, used for redirection or memory buffers
import re                                                                               # Regular expressions for pattern matching
import csv                                                                              # Read/write CSV files
import time                                                                             # Timing utilities and sleep delays
import json                                                                             # JSON file and string handling
import glob                                                                             # Pattern-based file search (e.g., *.csv)
import shutil                                                                           # File copy/move/delete utilities
import logging                                                                          # Logging interface (configured in C03_logging_handler)
import threading                                                                        # Lightweight concurrent execution
import platform                                                                         # Detect OS details (Windows, macOS, Linux)
import contextlib                                                                       # Context manager utilities (e.g., suppress, redirect)
import subprocess                                                                       # Run shell commands or external processes
import calendar                                                                         # Calendar calculations (e.g., month/day lookups)
import datetime as dt                                                                   # Primary datetime module with alias 'dt'
import tkinter as tk                                                                    # Built-in GUI toolkit (install `python3-tk` only if missing on Linux)
import zipfile                                                                          # Read/write ZIP archives
import tempfile                                                                         # Create and manage temporary files/directories safely
import getpass                                                                          # Retrieve the current system username (used for WSL and user detection)
import pickle                                                                           # Standard library for serialising Python objects

from datetime import date, timedelta, datetime                                          # Commonly used datetime classes
from typing import Dict, List, Tuple, Optional, Any, Literal                            # Type hints for readability and safety
from tkinter import ttk, messagebox, filedialog, font as tkFont                         # Common Tkinter submodules for GUI building
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed    # tqdm provides visual progress bars for loops and task execution

# ====================================================================================================
# 4. OTHER THIRD-PARTY IMPORTS
# ----------------------------------------------------------------------------------------------------
# External libraries that are useful across multiple projects but not part of Python’s standard library.
# Only include packages that are genuinely reusable and non-domain-specific (e.g. pandas, numpy).
# If a project does not need one of these, it can still import this file safely — unused imports do no harm.
# ====================================================================================================
import pandas as pd                             # (pip install pandas) Data analysis and tabular data handling
import numpy as np                              # (comes with pandas) Fast numerical operations and arrays
import pdfplumber                               # (pip install pdfplumber) Accurate PDF text/table extraction
import snowflake.connector                      # (pip install snowflake-connector-python) Connect to Snowflake DWH
import openpyxl                                 # (pip install openpyxl) Read/write Excel .xlsx files
import PyPDF2                                   # (pip install PyPDF2) PDF manipulation (merge/split/metadata)
import requests                                 # (pip install requests) HTTP requests for APIs and downloads
import yaml                                     # (pip install pyyaml) Read and write YAML configuration files (.yaml / .yml)

from tkcalendar import DateEntry                # (pip install tkcalendar) Calendar/date-picker widget for Tkinter GUIs
from pdfminer.high_level import extract_text    # (installed with pdfplumber) Fallback PDF text extraction
from tqdm import tqdm                           # (pip install tqdm) Progress bars for long-running loops/tasks

# ====================================================================================================
# 5. WEB & AUTOMATION IMPORTS
# ----------------------------------------------------------------------------------------------------
# (pip install selenium webdriver-manager)
# Browser automation and scraping utilities for platforms such as JustEat, PayPal, or UberEats.
# Centralised here since Selenium is commonly reused across multiple projects.
# ====================================================================================================
from selenium import webdriver                                    # Core browser automation API
from selenium.webdriver.common.by import By                       # Element location strategies (ID, XPATH, CSS, etc.)
from selenium.webdriver.common.keys import Keys                   # Keyboard input constants
from selenium.webdriver.chrome.options import Options              # Chrome configuration (headless, profiles, etc.)
from selenium.webdriver.support.ui import WebDriverWait            # Explicit wait handler
from selenium.webdriver.support import expected_conditions as EC   # Expected conditions for element states
from webdriver_manager.chrome import ChromeDriverManager           # Auto-downloads and manages ChromeDriver binaries

# ====================================================================================================
# 6. GOOGLE API & OAUTH IMPORTS
# ----------------------------------------------------------------------------------------------------
# (pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib)
# Imports for Google API authentication and service building.
# Keep these together so Google-related functionality is easy to find.
# ====================================================================================================
from google.auth.transport.requests import Request                                          # OAuth 2.0 transport and token refresh
from google.oauth2.credentials import Credentials                                           # Stores and refreshes Google OAuth tokens
from google_auth_oauthlib.flow import InstalledAppFlow                                      # Runs local OAuth flow for desktop apps
from googleapiclient.discovery import build                                                 # Builds Google API service clients
from googleapiclient.errors import HttpError                                                # Standard error class for Google API calls
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload    # Upload/download files to Google services