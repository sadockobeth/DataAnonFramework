"""
Module: execution_panel.py

Purpose:
Controls anonymization execution from the GUI.

Main responsibilities:
- Validate execution configuration.
- Prepare the OUT_PLACE target table.
- Handle an already-existing target table through user confirmation.
- Start ExecutionWorker in a background QThread.
- Display batch and row processing progress.
- Allow safe cooperative execution cancellation.
- Receive successful, cancelled, and failed execution results.
- Build and emit execution summaries.
- Notify MainWindow when execution starts and finishes.
- Protect the GUI from starting multiple simultaneous executions.
- Clear execution status when starting a new session.

This module does not transform source rows or perform batch INSERT
operations directly. Those operations are handled by ExecutionWorker.
"""

from oracledb import DatabaseError

from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox
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
    # SECTION 2: PANEL SIGNALS
    # ------------------------------------------------------------------
    # summary_ready:
    #     sends completed execution summary to MainWindow.
    #
    # execution_state_changed:
    #     True  -> execution started
    #     False -> execution finished
    summary_ready = Signal(object)
    execution_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 3: CREATE EXECUTION BUTTONS
        # ------------------------------------------------------------------
        self.execute_button = QPushButton("Execute Anonymization")
        self.execute_button.setObjectName("primaryButton")

        self.cancel_button = QPushButton("Cancel Execution")
        self.cancel_button.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 4: CREATE PROGRESS BAR
        # ------------------------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel("Ready to execute anonymization.")

        # ------------------------------------------------------------------
        # SECTION 6: STORE THREAD AND WORKER REFERENCES
        # ------------------------------------------------------------------
        self.thread = None
        self.worker = None

        # Current configuration is retained only while the execution is
        # active so the final execution summary can be constructed.
        self.current_source_config = None
        self.current_rules = None
        self.current_target_config = None

        # ------------------------------------------------------------------
        # SECTION 7: CREATE ACTION ROW
        # ------------------------------------------------------------------
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        action_layout.addStretch()
        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.execute_button)

        # ------------------------------------------------------------------
        # SECTION 8: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(
            QLabel(
                "Run the configured anonymization process and monitor "
                "its progress."
            )
        )

        layout.addWidget(QLabel("Execution Progress"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addLayout(action_layout)

        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 9: CONNECT INTERNAL GUI EVENTS
        # ------------------------------------------------------------------
        # Execute Anonymization remains connected through MainWindow because
        # MainWindow first collects configuration from Sections 1-4.
        self.cancel_button.clicked.connect(self.request_cancellation)

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
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )
            self.status_label.setText(
                "An anonymization execution is already running."
            )
            return

        # ------------------------------------------------------------------
        # SECTION 11: VALIDATE DATABASE CONNECTION
        # ------------------------------------------------------------------
        if connection_config is None:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )
            self.status_label.setText(
                "Execution cannot start. Test the database connection first."
            )
            return

        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE COMPLETE CONFIGURATION
        # ------------------------------------------------------------------
        validation_error = validate_configuration(
            source_config,
            rules,
            target_config
        )

        if validation_error:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )
            self.status_label.setText(
                f"Execution validation failed: {validation_error}"
            )

            logger.warning(
                "Execution stopped because configuration validation failed."
            )
            return

        # ------------------------------------------------------------------
        # SECTION 13: PREPARE OUT_PLACE TARGET TABLE
        # ------------------------------------------------------------------
        included_columns = self.prepare_target_table(
            connection_config,
            source_config,
            target_config
        )

        # None means target preparation failed or the user cancelled because
        # the target table already existed.
        if included_columns is None:
            return

        # ------------------------------------------------------------------
        # SECTION 14: STORE CURRENT EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        self.current_source_config = source_config
        self.current_rules = rules
        self.current_target_config = target_config

        # ------------------------------------------------------------------
        # SECTION 15: START BACKGROUND WORKER
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
        # SECTION 16: READ TARGET-PREPARATION CONFIGURATION
        # ------------------------------------------------------------------
        source_schema = source_config["source_schema"]
        source_table = source_config["source_table"]

        target_schema = target_config["target_schema"]
        target_table = target_config["target_table"]
        excluded_columns = target_config["excluded_columns"]

        available_columns = [
            column["column_name"]
            for column in source_config["table_columns"]
        ]

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 17: CONNECT FOR TARGET DDL
            # ------------------------------------------------------------------
            # Target preparation remains in the GUI thread because an existing
            # target requires an interactive QMessageBox confirmation.
            connection = connect_to_oracle(connection_config)

            # ------------------------------------------------------------------
            # SECTION 18: CREATE EMPTY TARGET TABLE
            # ------------------------------------------------------------------
            try:
                included_columns = create_target_table(
                    connection,
                    source_schema,
                    source_table,
                    target_schema,
                    target_table,
                    available_columns,
                    excluded_columns
                )

            except DatabaseError as error:
                error_object = error.args[0]

                # --------------------------------------------------------------
                # SECTION 19: HANDLE TARGET ALREADY EXISTS
                # --------------------------------------------------------------
                # ORA-00955 means the target object already exists.
                if error_object.code != 955:
                    raise

                logger.info(
                    "Execution target already exists | Target=%s.%s",
                    target_schema,
                    target_table
                )

                answer = QMessageBox.question(
                    self,
                    "Target Table Already Exists",
                    f"Target table {target_schema}.{target_table} "
                    f"already exists.\n\n"
                    f"Do you want to drop and recreate it?",
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if answer != QMessageBox.StandardButton.Yes:
                    self.status_label.setStyleSheet("")
                    self.status_label.setText(
                        "Execution cancelled. Existing target table "
                        "was not changed."
                    )

                    logger.info(
                        "Execution cancelled because existing target "
                        "replacement was not approved."
                    )

                    return None

                # --------------------------------------------------------------
                # SECTION 20: DROP EXISTING TARGET
                # --------------------------------------------------------------
                drop_target_table(
                    connection,
                    target_schema,
                    target_table
                )

                logger.info(
                    "Existing execution target dropped | Target=%s.%s",
                    target_schema,
                    target_table
                )

                # --------------------------------------------------------------
                # SECTION 21: RECREATE EMPTY TARGET
                # --------------------------------------------------------------
                included_columns = create_target_table(
                    connection,
                    source_schema,
                    source_table,
                    target_schema,
                    target_table,
                    available_columns,
                    excluded_columns
                )

            # ------------------------------------------------------------------
            # SECTION 22: REPORT TARGET PREPARATION SUCCESS
            # ------------------------------------------------------------------
            logger.info(
                "Execution target prepared successfully | "
                "Source=%s.%s | Target=%s.%s | Columns=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                len(included_columns)
            )

            return included_columns

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 23: HANDLE TARGET PREPARATION FAILURE
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )
            self.status_label.setText(
                f"Unable to prepare target table: {error}"
            )

            logger.exception(
                "Target-table preparation failed | "
                "Source=%s.%s | Target=%s.%s",
                source_schema,
                source_table,
                target_schema,
                target_table
            )

            return None

        finally:
            # ------------------------------------------------------------------
            # SECTION 24: CLOSE TARGET-PREPARATION CONNECTION
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
        # SECTION 25: CREATE THREAD
        # ------------------------------------------------------------------
        self.thread = QThread()

        # ------------------------------------------------------------------
        # SECTION 26: CREATE EXECUTION WORKER
        # ------------------------------------------------------------------
        self.worker = ExecutionWorker(
            connection_config,
            source_config,
            rules,
            target_config,
            included_columns,
            batch_size=1000
        )

        self.worker.moveToThread(self.thread)

        # ------------------------------------------------------------------
        # SECTION 27: CONNECT THREAD AND WORKER SIGNALS
        # ------------------------------------------------------------------
        self.thread.started.connect(self.worker.run)

        self.worker.progress.connect(self.execution_progress)
        self.worker.completed.connect(self.execution_completed)
        self.worker.cancelled.connect(self.execution_cancelled)
        self.worker.failed.connect(self.execution_failed)

        # Worker always emits finished regardless of SUCCESS, CANCELLED
        # or FAILED.
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.execution_thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)

        # ------------------------------------------------------------------
        # SECTION 28: PREPARE GUI FOR ACTIVE EXECUTION
        # ------------------------------------------------------------------
        self.execute_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # We intentionally do not issue COUNT(*) before execution.
        #
        # A 0,0 QProgressBar displays Qt's busy/indeterminate progress mode.
        self.progress_bar.setRange(0, 0)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Anonymization execution started..."
        )

        # MainWindow uses this signal to disable configuration sections while
        # the background execution is active.
        self.execution_state_changed.emit(True)

        logger.info(
            "Background anonymization worker started."
        )

        # ------------------------------------------------------------------
        # SECTION 29: START BACKGROUND THREAD
        # ------------------------------------------------------------------
        self.thread.start()

    def execution_progress(
        self,
        batch_number,
        total_rows
    ):
        # ------------------------------------------------------------------
        # SECTION 30: DISPLAY EXECUTION PROGRESS
        # ------------------------------------------------------------------
        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"Processing batch {batch_number} | "
            f"{total_rows:,} rows processed"
        )

    def execution_completed(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 31: DISPLAY SUCCESSFUL EXECUTION
        # ------------------------------------------------------------------
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        rows_processed = execution_stats.get(
            "rows_processed",
            0
        )

        self.status_label.setStyleSheet(
            "color: green; font-weight: bold;"
        )

        self.status_label.setText(
            f"✓ Anonymization completed successfully. "
            f"{rows_processed:,} rows processed."
        )

        # ------------------------------------------------------------------
        # SECTION 32: BUILD EXECUTION SUMMARY
        # ------------------------------------------------------------------
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(summary)

    def execution_cancelled(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 33: DISPLAY CANCELLED EXECUTION
        # ------------------------------------------------------------------
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label.setStyleSheet(
            "color: #b26a00; font-weight: bold;"
        )

        self.status_label.setText(
            "Execution cancelled. Uncommitted rows were rolled back."
        )

        # ------------------------------------------------------------------
        # SECTION 34: BUILD CANCELLATION SUMMARY
        # ------------------------------------------------------------------
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(summary)

    def execution_failed(
        self,
        execution_stats
    ):
        # ------------------------------------------------------------------
        # SECTION 35: DISPLAY FAILED EXECUTION
        # ------------------------------------------------------------------
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        error = execution_stats.get(
            "error",
            "Unknown execution error."
        )

        self.status_label.setStyleSheet(
            "color: red; font-weight: bold;"
        )

        self.status_label.setText(
            f"Execution failed: {error}"
        )

        # ------------------------------------------------------------------
        # SECTION 36: BUILD FAILURE SUMMARY
        # ------------------------------------------------------------------
        summary = build_execution_summary(
            self.current_source_config,
            self.current_rules,
            self.current_target_config,
            execution_stats
        )

        self.summary_ready.emit(summary)

    def request_cancellation(self):
        # ------------------------------------------------------------------
        # SECTION 37: REQUEST SAFE EXECUTION CANCELLATION
        # ------------------------------------------------------------------
        if not self.is_execution_running():
            return

        # Do not use thread.terminate().
        #
        # requestInterruption() allows the worker to stop at a safe point,
        # roll back uncommitted Oracle DML, close the connection, and exit.
        self.thread.requestInterruption()

        self.cancel_button.setEnabled(False)

        self.status_label.setStyleSheet(
            "color: #b26a00; font-weight: bold;"
        )

        self.status_label.setText(
            "Cancellation requested. Waiting for safe rollback..."
        )

        logger.info(
            "Cooperative anonymization cancellation requested."
        )

    def execution_thread_finished(self):
        # ------------------------------------------------------------------
        # SECTION 38: RESTORE GUI AFTER THREAD FINISHES
        # ------------------------------------------------------------------
        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        # MainWindow re-enables the configuration sections.
        self.execution_state_changed.emit(False)

        logger.info(
            "Background anonymization worker thread finished."
        )

        # ------------------------------------------------------------------
        # SECTION 39: CLEAR THREAD REFERENCES
        # ------------------------------------------------------------------
        self.worker = None
        self.thread = None

        self.current_source_config = None
        self.current_rules = None
        self.current_target_config = None

    def is_execution_running(self):
        # ------------------------------------------------------------------
        # SECTION 40: REPORT EXECUTION STATE
        # ------------------------------------------------------------------
        return (
            self.thread is not None
            and self.thread.isRunning()
        )

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 41: PROTECT ACTIVE EXECUTION
        # ------------------------------------------------------------------
        if self.is_execution_running():
            return

        # ------------------------------------------------------------------
        # SECTION 42: CLEAR EXECUTION PANEL
        # ------------------------------------------------------------------
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Ready to execute anonymization."
        )

        self.current_source_config = None
        self.current_rules = None
        self.current_target_config = None