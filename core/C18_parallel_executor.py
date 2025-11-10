# ====================================================================================================
# C18_parallel_executor.py
# ----------------------------------------------------------------------------------------------------
# Provides reusable utilities for concurrent and parallel task execution.
#
# Purpose:
#   - Simplify running multiple tasks (functions) concurrently.
#   - Supports both multithreading (I/O-bound) and multiprocessing (CPU-bound) execution.
#   - Automatically handles logging, error capture, and result aggregation.
#
# Notes:
#   - All concurrency libraries are imported via C00_set_packages.py.
#   - Ideal for accelerating tasks such as API requests, file I/O, or batch processing.
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
# 3. CORE EXECUTION FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def run_in_parallel(
    func,
    tasks: list,
    mode: str = "thread",
    max_workers: int = 8,
    show_progress: bool = True,
) -> list:
    """
    Executes a list of tasks concurrently using threads or processes.

    Args:
        func (callable):
            The function to be executed for each task.
        tasks (list):
            List of items to pass into the function (each item is a separate task).
        mode (str):
            Execution mode — 'thread' (default) for I/O-bound, or 'process' for CPU-bound.
        max_workers (int):
            Maximum number of concurrent workers to use.
        show_progress (bool):
            Whether to display tqdm-style progress during execution.

    Returns:
        list:
            A list of results (in the same order as input tasks). Failed tasks return None.
    """
    if not callable(func):
        logger.error("❌ Provided function is not callable.")
        return []

    results = []
    executor_class = ThreadPoolExecutor if mode == "thread" else ProcessPoolExecutor
    logger.info(f"⚙️  Running {len(tasks)} tasks in parallel ({mode} mode, {max_workers} workers)...")

    try:
        with executor_class(max_workers=max_workers) as executor:
            futures = {executor.submit(func, t): t for t in tasks}

            iterator = as_completed(futures)
            if show_progress:
                iterator = tqdm(iterator, total=len(futures), desc="🚀 Running tasks", unit="task")

            for future in iterator:
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"❌ Task failed: {e}")
                    results.append(None)

        logger.info("✅ All parallel tasks complete.")
        return results

    except Exception as e:
        logger.error(f"❌ Error during parallel execution: {e}")
        return []


# ====================================================================================================
# 4. BATCH HELPERS
# ----------------------------------------------------------------------------------------------------
def chunk_tasks(task_list: list, chunk_size: int) -> list[list]:
    """
    Splits a list of tasks into evenly sized chunks.

    Args:
        task_list (list):
            The list of tasks to divide.
        chunk_size (int):
            Number of tasks per chunk.

    Returns:
        list[list]:
            List of smaller task lists (chunks).
    """
    if chunk_size <= 0:
        logger.error("❌ chunk_size must be greater than 0.")
        return []

    return [task_list[i : i + chunk_size] for i in range(0, len(task_list), chunk_size)]


def run_batches(func, all_tasks: list, chunk_size: int = 20, delay: float = 0.5) -> list:
    """
    Runs tasks in smaller sequential batches, optionally with a delay between them.

    Args:
        func (callable):
            Function to run for each task.
        all_tasks (list):
            The complete list of tasks to process.
        chunk_size (int):
            Number of tasks to run in each batch.
        delay (float):
            Pause (in seconds) between batches to avoid rate limits.

    Returns:
        list:
            Combined list of results from all batches.
    """
    all_results = []
    chunks = chunk_tasks(all_tasks, chunk_size)

    logger.info(f"🧩 Executing {len(chunks)} batches of {chunk_size} tasks each...")

    for i, chunk in enumerate(chunks, start=1):
        logger.info(f"▶️  Starting batch {i}/{len(chunks)}...")
        results = run_in_parallel(func, chunk, mode="thread", show_progress=False)
        all_results.extend(results)
        if i < len(chunks):
            time.sleep(delay)

    logger.info("✅ All batches complete.")
    return all_results


# ====================================================================================================
# 5. SELF TEST
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Runs a basic self-test to demonstrate threaded and batched execution using mock tasks.
    """
    logger.info("🔍 Running C18_parallel_executor self-test...")

    def mock_task(n):
        time.sleep(0.2)
        return f"Task {n} done"

    test_tasks = list(range(1, 11))

    results = run_in_parallel(mock_task, test_tasks, mode="thread", max_workers=5)
    logger.info(f"🧾 Threaded results: {results}")

    batched_results = run_batches(mock_task, test_tasks, chunk_size=4)
    logger.info(f"📦 Batched results: {batched_results}")

    logger.info("✅ C18_parallel_executor self-test complete.")
