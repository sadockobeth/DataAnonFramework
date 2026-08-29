"""
Module: log_manager.py

Purpose:
Provides persistent application logging and execution-history storage
for DataAnonFramework.

Main responsibilities:
- Create and manage the application's logs directory.
- Write technical application events to dataanonframework.log.
- Save anonymization execution summaries as persistent history records.
- Load recent execution-history records for display in the GUI.
- Convert execution datetime values into JSON-compatible text.
- Keep logging and execution-history storage separate from GUI logic.

This module does not store database credentials, access Oracle,
perform anonymization, or create GUI widgets.
"""

import json
import logging
from collections import deque
from pathlib import Path


# ------------------------------------------------------------------
# SECTION 1: DEFINE PROJECT AND LOG LOCATIONS
# ------------------------------------------------------------------
# __file__ points to:
# DataAnonFramework/app_logging/log_manager.py
#
# parent.parent therefore points to:
# DataAnonFramework/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# All application log files are stored under:
# DataAnonFramework/logs/
LOG_DIRECTORY = PROJECT_ROOT / "logs"

# Create the logs directory automatically if it does not already exist.
LOG_DIRECTORY.mkdir(exist_ok=True)

# Technical application log.
APPLICATION_LOG_FILE = LOG_DIRECTORY / "dataanonframework.log"

# Structured anonymization execution-history file.
EXECUTION_HISTORY_FILE = LOG_DIRECTORY / "execution_history.jsonl"


# ------------------------------------------------------------------
# SECTION 2: CONFIGURE APPLICATION LOGGER
# ------------------------------------------------------------------
# Create one shared logger for the complete DataAnonFramework application.
application_logger = logging.getLogger("DataAnonFramework")

# INFO means INFO, WARNING, ERROR, and CRITICAL messages will be recorded.
application_logger.setLevel(logging.INFO)

# Prevent messages from also being passed to Python's root logger.
application_logger.propagate = False

# Avoid creating duplicate file handlers if this module is imported
# multiple times during the same application session.
if not application_logger.handlers:
    file_handler = logging.FileHandler(
        APPLICATION_LOG_FILE,
        encoding="utf-8"
    )

    # Each technical log entry will contain:
    # timestamp | log level | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    application_logger.addHandler(file_handler)


def get_logger():
    # ------------------------------------------------------------------
    # SECTION 3: RETURN SHARED APPLICATION LOGGER
    # ------------------------------------------------------------------
    # Other DataAnonFramework modules can call get_logger() instead of
    # creating their own logging configuration.
    return application_logger


def save_execution_summary(summary):
    # ------------------------------------------------------------------
    # SECTION 4: PREPARE EXECUTION HISTORY RECORD
    # ------------------------------------------------------------------
    # Execution summaries contain datetime objects. JSON cannot store
    # datetime objects directly, therefore convert them into ISO text.
    history_record = {
        "status": summary["status"],
        "source": summary["source"],
        "target": summary["target"],
        "rows_processed": summary["rows_processed"],
        "batches_processed": summary["batches_processed"],
        "batch_size": summary["batch_size"],
        "rules": summary["rules"],
        "excluded_columns": summary["excluded_columns"],
        "started_at": summary["started_at"].isoformat(),
        "completed_at": summary["completed_at"].isoformat(),
        "duration_seconds": summary["duration_seconds"],
        "error": summary["error"]
    }

    try:
        # ------------------------------------------------------------------
        # SECTION 5: SAVE EXECUTION HISTORY
        # ------------------------------------------------------------------
        # JSON Lines stores one complete JSON object on each line.
        #
        # "a" means append mode, so previous execution records are preserved.
        with open(EXECUTION_HISTORY_FILE, "a", encoding="utf-8") as history_file:
            history_file.write(json.dumps(history_record) + "\n")

        # ------------------------------------------------------------------
        # SECTION 6: WRITE EXECUTION EVENT TO TECHNICAL LOG
        # ------------------------------------------------------------------
        # Store only operational information.
        # Database usernames, passwords, hostnames, and other connection
        # credentials are intentionally not written here.
        application_logger.info(
            "Execution %s | Source=%s | Target=%s | Rows=%s | Batches=%s | Duration=%.2fs",
            summary["status"],
            summary["source"],
            summary["target"],
            summary["rows_processed"],
            summary["batches_processed"],
            summary["duration_seconds"]
        )

        return True

    except Exception as error:
        # ------------------------------------------------------------------
        # SECTION 7: HANDLE HISTORY STORAGE FAILURE
        # ------------------------------------------------------------------
        # exception() records the error message and Python traceback in
        # dataanonframework.log for troubleshooting.
        application_logger.exception(
            "Failed to save execution history: %s",
            error
        )

        return False


def load_execution_history(limit=50):
    # ------------------------------------------------------------------
    # SECTION 8: CHECK EXECUTION HISTORY FILE
    # ------------------------------------------------------------------
    # No execution-history file simply means no execution has yet
    # been recorded.
    if not EXECUTION_HISTORY_FILE.exists():
        return []

    # deque(maxlen=limit) ensures only the most recent records are kept
    # in memory even if the history file eventually contains many records.
    recent_records = deque(maxlen=limit)

    try:
        # ------------------------------------------------------------------
        # SECTION 9: READ EXECUTION HISTORY
        # ------------------------------------------------------------------
        with open(EXECUTION_HISTORY_FILE, "r", encoding="utf-8") as history_file:
            for line in history_file:
                line = line.strip()

                # Ignore blank lines.
                if not line:
                    continue

                # Convert each JSON line back into a Python dictionary.
                recent_records.append(json.loads(line))

        # ------------------------------------------------------------------
        # SECTION 10: RETURN MOST RECENT EXECUTIONS FIRST
        # ------------------------------------------------------------------
        # The file is stored oldest -> newest.
        # The GUI should display newest -> oldest.
        return list(reversed(recent_records))

    except Exception as error:
        # ------------------------------------------------------------------
        # SECTION 11: HANDLE HISTORY READ FAILURE
        # ------------------------------------------------------------------
        application_logger.exception(
            "Failed to load execution history: %s",
            error
        )

        return []