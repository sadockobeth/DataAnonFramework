"""
Module: execution_worker.py

Purpose:
Performs anonymization execution in a background QThread.

Main responsibilities:
- Create its own Oracle connection inside the worker thread.
- Read source data in batches.
- Transform source rows using configured anonymization rules.
- Insert transformed rows into the OUT_PLACE target table in batches.
- Report execution progress to the GUI.
- Support cooperative cancellation.
- Commit only after the complete execution succeeds.
- Roll back all uncommitted DML when execution fails or is cancelled.
- Return execution statistics to ExecutionPanel.
- Close the worker database connection safely.

This module does not create or drop target tables, display GUI dialogs,
or manage the QThread lifecycle.
"""

from datetime import datetime
from time import perf_counter

from PySide6.QtCore import QObject, Signal, QThread

from database.oracle_connection import connect_to_oracle
from database.data_reader import read_rows_in_batches
from database.data_writer import insert_rows_batch
from anonymization.row_transformation_manager import transform_row
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
logger = get_logger()


class ExecutionCancelled(Exception):
    """Raised internally when cooperative execution cancellation is requested."""
    pass


class ExecutionWorker(QObject):

    # ------------------------------------------------------------------
    # SECTION 2: WORKER SIGNALS
    # ------------------------------------------------------------------
    progress = Signal(int, int)
    completed = Signal(object)
    cancelled = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(
        self,
        connection_config,
        source_config,
        rules,
        target_config,
        included_columns,
        batch_size=1000
    ):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 3: STORE EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        self.connection_config = connection_config
        self.source_config = source_config
        self.rules = rules
        self.target_config = target_config
        self.included_columns = included_columns
        self.batch_size = batch_size

    def check_cancellation(self):
        # ------------------------------------------------------------------
        # SECTION 4: CHECK FOR COOPERATIVE CANCELLATION
        # ------------------------------------------------------------------
        current_thread = QThread.currentThread()

        if current_thread.isInterruptionRequested():
            raise ExecutionCancelled()

    def build_execution_stats(
        self,
        status,
        rows_processed,
        batches_processed,
        started_at,
        start_time,
        error=None
    ):
        # ------------------------------------------------------------------
        # SECTION 5: BUILD EXECUTION STATISTICS
        # ------------------------------------------------------------------
        completed_at = datetime.now()
        duration_seconds = round(perf_counter() - start_time, 3)

        # IMPORTANT:
        #
        # Keep started_at and completed_at as datetime objects here.
        #
        # log_manager.py is responsible for converting datetime values
        # to ISO-format strings when execution history is written to JSON.
        return {
            "status": status,
            "rows_processed": rows_processed,
            "batches_processed": batches_processed,
            "batch_size": self.batch_size,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration_seconds,
            "error": error
        }

    def run(self):
        # ------------------------------------------------------------------
        # SECTION 6: INITIALIZE EXECUTION
        # ------------------------------------------------------------------
        connection = None
        batch_number = 0
        total_rows = 0

        started_at = datetime.now()
        start_time = perf_counter()

        source_schema = self.source_config["source_schema"]
        source_table = self.source_config["source_table"]

        target_schema = self.target_config["target_schema"]
        target_table = self.target_config["target_table"]

        try:
            # ------------------------------------------------------------------
            # SECTION 7: CREATE WORKER DATABASE CONNECTION
            # ------------------------------------------------------------------
            connection = connect_to_oracle(
                self.connection_config
            )

            self.check_cancellation()

            logger.info(
                "Anonymization execution started | "
                "Source=%s.%s | Target=%s.%s | BatchSize=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                self.batch_size
            )

            # ------------------------------------------------------------------
            # SECTION 8: READ SOURCE DATA IN BATCHES
            # ------------------------------------------------------------------
            for batch in read_rows_in_batches(
                connection,
                source_schema,
                source_table,
                batch_size=self.batch_size
            ):
                self.check_cancellation()

                transformed_rows = []

                # ------------------------------------------------------------------
                # SECTION 9: TRANSFORM CURRENT BATCH
                # ------------------------------------------------------------------
                for row in batch:
                    self.check_cancellation()

                    transformed_rows.append(
                        transform_row(
                            row,
                            self.rules
                        )
                    )

                self.check_cancellation()

                # ------------------------------------------------------------------
                # SECTION 10: WRITE CURRENT BATCH
                # ------------------------------------------------------------------
                insert_rows_batch(
                    connection,
                    target_schema,
                    target_table,
                    transformed_rows,
                    self.included_columns
                )

                self.check_cancellation()

                batch_number += 1
                total_rows += len(batch)

                self.progress.emit(
                    batch_number,
                    total_rows
                )

            # ------------------------------------------------------------------
            # SECTION 11: FINAL CANCELLATION CHECK
            # ------------------------------------------------------------------
            self.check_cancellation()

            # ------------------------------------------------------------------
            # SECTION 12: COMMIT COMPLETE EXECUTION
            # ------------------------------------------------------------------
            connection.commit()

            execution_stats = self.build_execution_stats(
                status="SUCCESS",
                rows_processed=total_rows,
                batches_processed=batch_number,
                started_at=started_at,
                start_time=start_time
            )

            logger.info(
                "Anonymization execution completed successfully | "
                "Source=%s.%s | Target=%s.%s | Rows=%s | Batches=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                total_rows,
                batch_number
            )

            self.completed.emit(
                execution_stats
            )

        except ExecutionCancelled:
            # ------------------------------------------------------------------
            # SECTION 13: HANDLE EXECUTION CANCELLATION
            # ------------------------------------------------------------------
            if connection is not None:
                connection.rollback()

            execution_stats = self.build_execution_stats(
                status="CANCELLED",
                rows_processed=total_rows,
                batches_processed=batch_number,
                started_at=started_at,
                start_time=start_time
            )

            logger.info(
                "Anonymization execution cancelled | "
                "Source=%s.%s | Target=%s.%s | "
                "ProcessedRowsBeforeRollback=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                total_rows
            )

            self.cancelled.emit(
                execution_stats
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 14: HANDLE EXECUTION FAILURE
            # ------------------------------------------------------------------
            if connection is not None:
                connection.rollback()

            execution_stats = self.build_execution_stats(
                status="FAILED",
                rows_processed=total_rows,
                batches_processed=batch_number,
                started_at=started_at,
                start_time=start_time,
                error=str(error)
            )

            logger.exception(
                "Anonymization execution failed | "
                "Source=%s.%s | Target=%s.%s",
                source_schema,
                source_table,
                target_schema,
                target_table
            )

            self.failed.emit(
                execution_stats
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 15: CLOSE WORKER DATABASE CONNECTION
            # ------------------------------------------------------------------
            if connection is not None:
                connection.close()

            # ------------------------------------------------------------------
            # SECTION 16: NOTIFY THREAD LIFECYCLE
            # ------------------------------------------------------------------
            self.finished.emit()