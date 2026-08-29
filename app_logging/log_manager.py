"""
Module: log_manager.py

Purpose:
Provides persistent application logging and execution-history storage
for the Data Anonymization Engine.

Main responsibilities:
- Create and manage the application's logs directory.
- Write technical application events to a rotating technical log file.
- Prevent the technical log from growing indefinitely.
- Keep a limited number of previous technical log files.
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
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ------------------------------------------------------------------
# SECTION 1: DEFINE PROJECT AND LOG LOCATIONS
# ------------------------------------------------------------------
# __file__ points to:
#
# DataAnonFramework/app_logging/log_manager.py
#
# parent.parent therefore points to the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Store all logging-related files under:
#
# DataAnonFramework/logs/
LOG_DIRECTORY = PROJECT_ROOT / "logs"

# Create the logs directory automatically if it does not already exist.
LOG_DIRECTORY.mkdir(exist_ok=True)

# Technical application log.
APPLICATION_LOG_FILE = LOG_DIRECTORY / "dataanonframework.log"

# Structured anonymization execution-history file.
EXECUTION_HISTORY_FILE = LOG_DIRECTORY / "execution_history.jsonl"


# ------------------------------------------------------------------
# SECTION 2: DEFINE TECHNICAL LOG ROTATION SETTINGS
# ------------------------------------------------------------------
# Maximum size of the active technical log file:
#
# 5 * 1024 * 1024 = 5 MB
MAX_LOG_FILE_SIZE = 5 * 1024 * 1024

# Keep five previous technical log files.
#
# Example:
#
# dataanonframework.log
# dataanonframework.log.1
# dataanonframework.log.2
# dataanonframework.log.3
# dataanonframework.log.4
# dataanonframework.log.5
LOG_BACKUP_COUNT = 5


# ------------------------------------------------------------------
# SECTION 3: CONFIGURE APPLICATION LOGGER
# ------------------------------------------------------------------
# Create one shared logger for the complete application.
application_logger = logging.getLogger(
    "DataAnonymizationEngine"
)

# INFO means the logger records:
#
# INFO
# WARNING
# ERROR
# CRITICAL
application_logger.setLevel(
    logging.INFO
)

# Prevent messages from also being passed to Python's root logger.
application_logger.propagate = False

# Avoid creating duplicate file handlers if this module is imported
# multiple times during the same application session.
if not application_logger.handlers:

    # ------------------------------------------------------------------
    # SECTION 4: CREATE ROTATING FILE HANDLER
    # ------------------------------------------------------------------
    # RotatingFileHandler automatically rotates the active log when
    # it reaches MAX_LOG_FILE_SIZE.
    file_handler = RotatingFileHandler(
        APPLICATION_LOG_FILE,
        maxBytes=MAX_LOG_FILE_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )

    # Each technical log entry contains:
    #
    # timestamp | log level | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(
        formatter
    )

    application_logger.addHandler(
        file_handler
    )


def get_logger():
    # ------------------------------------------------------------------
    # SECTION 5: RETURN SHARED APPLICATION LOGGER
    # ------------------------------------------------------------------
    # Other modules call get_logger() instead of creating their own
    # logging configuration.
    return application_logger


def save_execution_summary(summary):
    # ------------------------------------------------------------------
    # SECTION 6: PREPARE EXECUTION HISTORY RECORD
    # ------------------------------------------------------------------
    # Execution summaries contain datetime objects.
    #
    # JSON cannot store datetime objects directly, therefore convert
    # them into ISO-formatted text.
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
        # SECTION 7: SAVE EXECUTION HISTORY
        # ------------------------------------------------------------------
        # JSON Lines stores one complete JSON object on each line.
        #
        # Append mode preserves all previous execution-history records.
        with open(
            EXECUTION_HISTORY_FILE,
            "a",
            encoding="utf-8"
        ) as history_file:

            history_file.write(
                json.dumps(history_record) + "\n"
            )

        # ------------------------------------------------------------------
        # SECTION 8: WRITE EXECUTION EVENT TO TECHNICAL LOG
        # ------------------------------------------------------------------
        # Only operational information is recorded.
        #
        # Database credentials and source row values are intentionally
        # not written to the technical log.
        application_logger.info(
            "Execution %s | Source=%s | Target=%s | "
            "Rows=%s | Batches=%s | Duration=%.2fs",
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
        # SECTION 9: HANDLE HISTORY STORAGE FAILURE
        # ------------------------------------------------------------------
        # exception() records both the error and Python traceback.
        application_logger.exception(
            "Failed to save execution history: %s",
            error
        )

        return False


def load_execution_history(limit=50):
    # ------------------------------------------------------------------
    # SECTION 10: CHECK EXECUTION HISTORY FILE
    # ------------------------------------------------------------------
    # If no execution-history file exists yet, simply return an empty list.
    if not EXECUTION_HISTORY_FILE.exists():
        return []

    # deque(maxlen=limit) keeps only the most recent requested records
    # in memory, even if the history file contains many executions.
    recent_records = deque(
        maxlen=limit
    )

    try:
        # ------------------------------------------------------------------
        # SECTION 11: READ EXECUTION HISTORY
        # ------------------------------------------------------------------
        with open(
            EXECUTION_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as history_file:

            for line in history_file:
                line = line.strip()

                # Ignore blank lines.
                if not line:
                    continue

                # Convert the JSON line back into a Python dictionary.
                recent_records.append(
                    json.loads(line)
                )

        # ------------------------------------------------------------------
        # SECTION 12: RETURN MOST RECENT EXECUTIONS FIRST
        # ------------------------------------------------------------------
        # The file is stored oldest -> newest.
        #
        # The GUI displays newest -> oldest.
        return list(
            reversed(recent_records)
        )

    except Exception as error:
        # ------------------------------------------------------------------
        # SECTION 13: HANDLE HISTORY READ FAILURE
        # ------------------------------------------------------------------
        application_logger.exception(
            "Failed to load execution history: %s",
            error
        )

        return []