"""
Module: execution_panel.py

Purpose:
Manages OUT_PLACE anonymization execution from the GUI while keeping
long-running row processing outside the main GUI thread.

Main responsibilities:
- Use the successfully tested GUI database connection configuration.
- Validate the complete anonymization configuration.
- Create the OUT_PLACE target table.
- Ask for confirmation before replacing an existing target table.
- Create and manage QThread and ExecutionWorker.
- Display execution progress using a QProgressBar and status messages.
- Prevent duplicate execution while processing is already running.
- Allow the user to request safe cooperative cancellation.
- Receive successful, failed, and cancelled worker results.
- Notify MainWindow when execution starts and stops.
- Build and publish execution summaries.
- Record important execution events in the technical log.
- Clear execution status only when no worker is active.

Heavy row reading, transformation, batch insertion, commit, rollback,
and cancellation handling are performed by execution_worker.py.

This module does not forcibly terminate worker threads, log database
credentials, or log source row values.
"""

from oracledb import DatabaseError

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QProgressBar
)

from database.oracle_connection import connect_to_oracle
from database.target_table_manager import create_target_table, drop_target_table
from validation.configuration_validator import validate_configuration
from reporting.execution_summary import build_execution_summary
from gui.execution_worker import ExecutionWorker
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
logger = get_logger()


class ExecutionPanel(QWidget):

    # ------------------------------------------------------------------
    # SIGNAL: EXECUTION SUMMARY READY
    # ------------------------------------------------------------------
    summary_ready = Signal(object)

    # ------------------------------------------------------------------
    # SIGNAL: EXECUTION STATE CHANGED
    # ------------------------------------------------------------------
    execution_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: INITIALIZE THREAD OBJECTS
        # ------------------------------------------------------------------
        self.thread = None
        self.worker = None

        self.current_source_config = None
        self.current_rules = None
        self.current_target_config = None

        # ------------------------------------------------------------------
        # SECTION 3: CREATE EXECUTION BUTTON
        # ------------------------------------------------------------------
        self.execute_button = QPushButton(
            "Execute Anonymization"
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE CANCEL BUTTON
        # ------------------------------------------------------------------
        # Cancellation is available only while a worker is running.
        self.cancel_button = QPushButton(
            "Cancel Execution"
        )

        self.cancel_button.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 5: CREATE PROGRESS BAR
        # ------------------------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # ------------------------------------------------------------------
        # SECTION 6: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Execution not yet started."
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        layout.addWidget(
            self.execute_button
        )

        layout.addWidget(
            self.cancel_button
        )

        layout.addWidget(
            self.progress_bar
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 8: CONNECT CANCEL BUTTON
        # ------------------------------------------------------------------
        self.cancel_button.clicked.connect(
            self.request_cancellation
        )

    def is_execution_running(self):
        # ------------------------------------------------------------------
        # SECTION 9: RETURN CURRENT EXECUTION STATE
        # ------------------------------------------------------------------
        return (
            self.thread is not None and
            self.thread.isRunning()
        )

    def run_execution(
        self,
        connection_config,
        source_config,
        rules,
        target_config
    ):
        # ------------------------------------------------------------------
        # SECTION 10: PREVENT DUPLICATE EXECUTION
        # ------------------------------------------------------------------
        if self.is_execution_running():
            logger.warning(
                "Execution request rejected because another anonymization "
                "execution is already running."
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Execution is already running."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 11: VALIDATE GUI DATABASE CONNECTION
        # ------------------------------------------------------------------
        if connection_config is None:
            logger.warning(
                "Execution stopped because no tested GUI database "
                "connection was available."
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Execution stopped: Test the database connection first."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE CONFIGURATION
        # ------------------------------------------------------------------
        validation_error = validate_configuration(
            source_config,
            rules,
            target_config
        )

        if validation_error:
            logger.warning(
                "Execution validation failed | Source=%s.%s | Reason=%s",
                source_config.get("source_schema", ""),
                source_config.get("source_table", ""),
                validation_error
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Execution stopped: {validation_error}"
            )

            return

        # ------------------------------------------------------------------
        # SECTION 13: LOG ACCEPTED EXECUTION REQUEST
        # ------------------------------------------------------------------
        logger.info(
            "Execution request accepted | Source=%s.%s | Target=%s.%s | "
            "Rules=%s | ExcludedColumns=%s",
            source_config["source_schema"],
            source_config["source_table"],
            target_config["target_schema"],
            target_config["target_table"],
            len(rules),
            len(target_config["excluded_columns"])
        )

        # ------------------------------------------------------------------
        # SECTION 14: PREPARE TARGET TABLE
        # ------------------------------------------------------------------
        included_columns = self.prepare_target_table(
            connection_config,
            source_config,
            target_config
        )

        if included_columns is None:
            return

        # ------------------------------------------------------------------
        # SECTION 15: START BACKGROUND EXECUTION
        # ------------------------------------------------------------------
        self.start_worker(
            connection_config,
            source_config,
            rules,
            target_config,
            included_columns
        )

    def prepare_target_table(
        self,
        connection_config,
        source_config,
        target_config
    ):
        # ------------------------------------------------------------------
        # SECTION 16: READ TARGET CONFIGURATION
        # ------------------------------------------------------------------
        source_schema = source_config["source_schema"]
        source_table = source_config["source_table"]

        target_schema = target_config["target_schema"]
        target_table = target_config["target_table"]

        excluded_columns = target_config["excluded_columns"]

        source_columns = [
            column["column_name"]
            for column in source_config["table_columns"]
        ]

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 17: CONNECT FOR TARGET PREPARATION
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")
            self.status_label.setText(
                "Preparing target table..."
            )

            connection = connect_to_oracle(
                connection_config
            )

            try:
                # --------------------------------------------------------------
                # SECTION 18: CREATE TARGET TABLE
                # --------------------------------------------------------------
                included_columns = create_target_table(
                    connection,
                    source_schema,
                    source_table,
                    target_schema,
                    target_table,
                    source_columns,
                    excluded_columns
                )

                logger.info(
                    "Target table created successfully | Source=%s.%s | "
                    "Target=%s.%s | IncludedColumns=%s | ExcludedColumns=%s",
                    source_schema,
                    source_table,
                    target_schema,
                    target_table,
                    len(included_columns),
                    len(excluded_columns)
                )

            except DatabaseError as error:
                # --------------------------------------------------------------
                # SECTION 19: INSPECT ORACLE ERROR
                # --------------------------------------------------------------
                error_object = error.args[0]

                if error_object.code != 955:
                    raise

                logger.warning(
                    "Target table already exists | Target=%s.%s",
                    target_schema,
                    target_table
                )

                # --------------------------------------------------------------
                # SECTION 20: CONFIRM TARGET REPLACEMENT
                # --------------------------------------------------------------
                answer = QMessageBox.question(
                    self,
                    "Target Table Already Exists",
                    f"{target_schema}.{target_table} already exists.\n\n"
                    f"Drop and recreate it?",
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No
                )

                if answer != QMessageBox.StandardButton.Yes:
                    logger.info(
                        "Execution cancelled because existing target table "
                        "was preserved | Target=%s.%s",
                        target_schema,
                        target_table
                    )

                    self.status_label.setStyleSheet("")

                    self.status_label.setText(
                        "Execution cancelled. Existing target table "
                        "was not changed."
                    )

                    return None

                # --------------------------------------------------------------
                # SECTION 21: DROP EXISTING TARGET TABLE
                # --------------------------------------------------------------
                logger.info(
                    "User approved replacement of existing target table | "
                    "Target=%s.%s",
                    target_schema,
                    target_table
                )

                drop_target_table(
                    connection,
                    target_schema,
                    target_table
                )

                logger.info(
                    "Existing target table dropped successfully | "
                    "Target=%s.%s",
                    target_schema,
                    target_table
                )

                # --------------------------------------------------------------
                # SECTION 22: RECREATE TARGET TABLE
                # --------------------------------------------------------------
                included_columns = create_target_table(
                    connection,
                    source_schema,
                    source_table,
                    target_schema,
                    target_table,
                    source_columns,
                    excluded_columns
                )

                logger.info(
                    "Target table recreated successfully | Target=%s.%s | "
                    "IncludedColumns=%s | ExcludedColumns=%s",
                    target_schema,
                    target_table,
                    len(included_columns),
                    len(excluded_columns)
                )

            return included_columns

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 23: HANDLE TARGET PREPARATION FAILURE
            # ------------------------------------------------------------------
            logger.exception(
                "Target preparation failed | Source=%s.%s | "
                "Target=%s.%s | Error=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                error
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Target preparation failed: {error}"
            )

            return None

        finally:
            # ------------------------------------------------------------------
            # SECTION 24: CLOSE TARGET CONNECTION
            # ------------------------------------------------------------------
            if connection is not None:
                connection.close()

    def start_worker(
        self,
        connection_config,
        source_config,
        rules,
        target_config,
        included_columns
    ):
        # ------------------------------------------------------------------
        # SECTION 25: STORE CURRENT EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        self.current_source_config = source_config.copy()
        self.current_rules = rules.copy()
        self.current_target_config = target_config.copy()

        # ------------------------------------------------------------------
        # SECTION 26: CREATE QTHREAD
        # ------------------------------------------------------------------
        self.thread = QThread(self)

        # ------------------------------------------------------------------
        # SECTION 27: CREATE WORKER
        # ------------------------------------------------------------------
        self.worker = ExecutionWorker(
            connection_config,
            source_config,
            rules,
            target_config,
            included_columns,
            batch_size=1000
        )

        self.worker.moveToThread(
            self.thread
        )

        # ------------------------------------------------------------------
        # SECTION 28: CONNECT WORKER SIGNALS
        # ------------------------------------------------------------------
        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.update_progress
        )

        self.worker.completed.connect(
            self.execution_completed
        )

        self.worker.cancelled.connect(
            self.execution_cancelled
        )

        self.worker.failed.connect(
            self.execution_failed
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread_finished
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        # ------------------------------------------------------------------
        # SECTION 29: PREPARE GUI FOR EXECUTION
        # ------------------------------------------------------------------
        self.execute_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Indeterminate progress while total row count is unknown.
        self.progress_bar.setRange(0, 0)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Execution running..."
        )

        # Protect configuration panels through MainWindow.
        self.execution_state_changed.emit(True)

        logger.info(
            "Background anonymization execution started | "
            "Source=%s.%s | Target=%s.%s | BatchSize=%s",
            source_config["source_schema"],
            source_config["source_table"],
            target_config["target_schema"],
            target_config["target_table"],
            1000
        )

        # ------------------------------------------------------------------
        # SECTION 30: START QTHREAD
        # ------------------------------------------------------------------
        self.thread.start()

    def request_cancellation(self):
        # ------------------------------------------------------------------
        # SECTION 31: REQUEST SAFE CANCELLATION
        # ------------------------------------------------------------------
        # requestInterruption() does not kill the worker.
        #
        # It sets an interruption flag that ExecutionWorker checks at safe
        # processing checkpoints.
        if not self.is_execution_running():
            return

        logger.warning(
            "User requested anonymization execution cancellation."
        )

        self.thread.requestInterruption()

        # Prevent repeated cancellation requests.
        self.cancel_button.setEnabled(False)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Cancellation requested. Waiting for safe rollback..."
        )

    def update_progress(
        self,
        batch_number,
        total_rows
    ):
        # ------------------------------------------------------------------
        # SECTION 32: DISPLAY PROGRESS
        # ------------------------------------------------------------------
        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"Processing batch {batch_number} - "
            f"{total_rows} rows processed."
        )

    def execution_completed(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 33: HANDLE SUCCESSFUL EXECUTION
        # ------------------------------------------------------------------
        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        total_rows = execution_stats["rows_processed"]

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"Execution completed successfully. "
            f"{total_rows} rows processed."
        )

        logger.info(
            "Background anonymization execution completed | "
            "Source=%s.%s | Target=%s.%s | Rows=%s | "
            "Batches=%s | Duration=%.2fs",
            self.current_source_config["source_schema"],
            self.current_source_config["source_table"],
            self.current_target_config["target_schema"],
            self.current_target_config["target_table"],
            execution_stats["rows_processed"],
            execution_stats["batches_processed"],
            execution_stats["duration_seconds"]
        )

        # ------------------------------------------------------------------
        # SECTION 34: BUILD SUCCESS SUMMARY
        # ------------------------------------------------------------------
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(
            summary
        )

    def execution_cancelled(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 35: HANDLE CANCELLED EXECUTION
        # ------------------------------------------------------------------
        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label.setStyleSheet(
            "color: orange; font-weight: bold;"
        )

        self.status_label.setText(
            "Execution cancelled. All uncommitted target rows were rolled back."
        )

        logger.warning(
            "Background anonymization execution cancelled | "
            "Source=%s.%s | Target=%s.%s | "
            "RowsBeforeRollback=%s | Batches=%s | Duration=%.2fs",
            self.current_source_config["source_schema"],
            self.current_source_config["source_table"],
            self.current_target_config["target_schema"],
            self.current_target_config["target_table"],
            execution_stats["rows_processed"],
            execution_stats["batches_processed"],
            execution_stats["duration_seconds"]
        )

        # ------------------------------------------------------------------
        # SECTION 36: BUILD CANCELLATION SUMMARY
        # ------------------------------------------------------------------
        # Cancellation is stored in execution history just like SUCCESS
        # and FAILED, giving us a complete operational history.
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(
            summary
        )

    def execution_failed(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 37: HANDLE EXECUTION FAILURE
        # ------------------------------------------------------------------
        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        error_message = execution_stats["error"]

        self.status_label.setStyleSheet(
            "color: red; font-weight: bold;"
        )

        self.status_label.setText(
            f"Execution failed: {error_message}"
        )

        logger.error(
            "Background anonymization execution failed | "
            "Source=%s.%s | Target=%s.%s | "
            "RowsBeforeRollback=%s | BatchesBeforeRollback=%s | Error=%s",
            self.current_source_config["source_schema"],
            self.current_source_config["source_table"],
            self.current_target_config["target_schema"],
            self.current_target_config["target_table"],
            execution_stats["rows_processed"],
            execution_stats["batches_processed"],
            error_message
        )

        # ------------------------------------------------------------------
        # SECTION 38: BUILD FAILURE SUMMARY
        # ------------------------------------------------------------------
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(
            summary
        )

    def thread_finished(self):
        # ------------------------------------------------------------------
        # SECTION 39: CLEAN UP THREAD REFERENCES
        # ------------------------------------------------------------------
        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.worker = None
        self.thread = None

        # Configuration and application close protection can now be released.
        self.execution_state_changed.emit(False)

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 40: CLEAR EXECUTION PANEL
        # ------------------------------------------------------------------
        if self.is_execution_running():
            logger.warning(
                "Execution panel clear request rejected because "
                "anonymization is currently running."
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Cannot clear execution status while processing is running."
            )

            return

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.current_source_config = None
        self.current_rules = None
        self.current_target_config = None

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Execution not yet started."
        )