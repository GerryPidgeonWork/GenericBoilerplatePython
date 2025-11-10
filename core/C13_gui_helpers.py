# ====================================================================================================
# C13_gui_helpers.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable GUI utilities and visual standards for all GenericBoilerplatePython projects.
#
# Purpose:
#   - Centralise common Tkinter operations (popups, loading bars, window layout helpers).
#   - Provide consistent fonts, colours, and visual behaviour across GUIs.
#   - Simplify building new interfaces (progress dialogs, message alerts, etc.).
#
# Usage:
#   from core.C13_gui_helpers import *
#
# Example:
#   >>> show_info("Process completed successfully!")
#   >>> with ProgressPopup(root, "Processing files...") as popup:
#   >>>     long_running_task()
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
from core.C07_datetime_utils import as_str                       # For timestamped labels or logs

# ====================================================================================================
# 3. GUI STYLE CONSTANTS
# ----------------------------------------------------------------------------------------------------
GUI_THEME = {
    "bg": "#F8F9FA",
    "fg": "#212529",
    "accent": "#0D6EFD",
    "success": "#198754",
    "warning": "#FFC107",
    "error": "#DC3545",
    "font": ("Segoe UI", 10),
    "font_bold": ("Segoe UI", 10, "bold"),
}


# ====================================================================================================
# 4. MESSAGE POPUPS
# ----------------------------------------------------------------------------------------------------
def show_info(message: str, title: str = "Information") -> None:
    """
    Display an informational message box.

    Args:
        message (str): Message text to display.
        title (str, optional): Window title. Defaults to "Information".
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
        logger.info(f"💬 Info: {message}")
    except Exception as e:
        log_exception(e, context="show_info")


def show_warning(message: str, title: str = "Warning") -> None:
    """
    Display a warning message box.

    Args:
        message (str): Message text to display.
        title (str, optional): Window title. Defaults to "Warning".
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(title, message)
        root.destroy()
        logger.warning(f"⚠️  Warning: {message}")
    except Exception as e:
        log_exception(e, context="show_warning")


def show_error(message: str, title: str = "Error") -> None:
    """
    Display an error message box.

    Args:
        message (str): Message text to display.
        title (str, optional): Window title. Defaults to "Error".
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
        logger.error(f"❌ Error: {message}")
    except Exception as e:
        log_exception(e, context="show_error")


# ====================================================================================================
# 5. PROGRESS POPUP CLASS
# ----------------------------------------------------------------------------------------------------
class ProgressPopup:
    """
    A reusable modal popup window with a progress bar and message label.

    Example:
        >>> with ProgressPopup(root, "Processing data...") as popup:
        >>>     for i in range(100):
        >>>         popup.update_progress(i+1, 100)
    """

    def __init__(self, parent: tk.Tk, message: str = "Processing..."):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Please wait")
        self.window.configure(bg=GUI_THEME["bg"])
        self.window.geometry("350x120")
        self.window.resizable(False, False)
        self.window.grab_set()

        # --- Label ---
        self.label = ttk.Label(self.window, text=message, font=GUI_THEME["font_bold"])
        self.label.pack(pady=10)

        # --- Progress bar ---
        self.progress = ttk.Progressbar(self.window, length=300, mode="determinate")
        self.progress.pack(pady=10)

        # --- Status text ---
        self.status_label = ttk.Label(self.window, text="", font=GUI_THEME["font"])
        self.status_label.pack()

        logger.info("🪄 ProgressPopup initialised.")

    def update_progress(self, current: int, total: int):
        """Update progress bar and status label."""
        try:
            percent = int((current / total) * 100)
            self.progress["value"] = percent
            self.status_label.config(text=f"{percent}% complete")
            self.window.update_idletasks()
        except Exception as e:
            log_exception(e, context="update_progress")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.window.destroy()
        logger.info("✅ ProgressPopup closed.")


# ====================================================================================================
# 6. THREAD-SAFE TASK WRAPPER
# ----------------------------------------------------------------------------------------------------
def run_in_thread(target, *args, **kwargs):
    """
    Run a blocking function in a background thread to keep the GUI responsive.

    Args:
        target (callable): The function to execute.
        *args: Positional arguments for the target.
        **kwargs: Keyword arguments for the target.

    Example:
        >>> run_in_thread(long_task, file_path)
    """
    import threading

    def wrapper():
        try:
            target(*args, **kwargs)
        except Exception as e:
            log_exception(e, context=f"Thread: {target.__name__}")

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    logger.info(f"🚀 Started thread for: {target.__name__}")
    return thread


# ====================================================================================================
# 7. MAIN EXECUTION (SANDBOXED TEST)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone sandboxed test for GUI helpers.
    Demonstrates message boxes and progress popup in isolation.
    """
    print("🔍 Running C13_gui_helpers self-test...")
    root = tk.Tk()
    root.withdraw()

    show_info("This is an info message.")
    show_warning("This is a warning message.")
    show_error("This is an error message.")

    with ProgressPopup(root, "Simulating progress...") as popup:
        for i in range(0, 101, 10):
            popup.update_progress(i, 100)
            time.sleep(0.1)

    root.destroy()
    print("✅ GUI helpers sandboxed test complete.")
