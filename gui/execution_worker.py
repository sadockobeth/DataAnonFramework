"""
Module: execution_worker.py

Purpose:
Performs long-running OUT_PLACE anonymization work in a background
thread so the GUI remains responsive during execution.

Main responsibilities:
- Connect to Oracle using the successfully tested GUI connection configuration.
- Read source rows in manageable batches.
- Apply anonymization rules using row_transformation_manager.py.
- Collect transformed rows into batches.
- Insert transformed batches efficiently using executemany().
- Track execution start time, completion time, batches, and processed rows.
- Report execution progress back to the GUI using Qt signals.
- Support cooperative execution cancellation using QThread interruption requests.
- Commit once after all batches complete successfully.
- Roll back all uncommitted inserts if processing fails or is cancelled.
- Record transaction-critical events in the technical log.
- Return execution statistics after success, failure, or cancellation.
- Notify QThread when worker processing finishes.

This module does not create GUI widgets, display message boxes,
create/drop target tables, implement anonymization algorithms,
or log source and transformed row values.
"""

from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot, QThread

from database.oracle_connection import connect_to_oracle
from database.data_reader import read_rows_in_batches
from database.data_writer import insert_rows_batch
from anonymization.row_transformation_manager import transform_row
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
# Use the shared DataAnonFramework technical logger.
#
# Source row values and transformed values are deliberately not logged.
logger = get_logger()


class ExecutionCancelled(Exception):
    # ------------------------------------------------------------------
    # INTERNAL EXCEPTION: EXECUTION CANCELLED
    # ------------------------------------------------------------------
    # This exception is used internally to leave the processing loop
    # cleanly when QThread receives an interruption request.
    #
    # It is different from a processing failure because cancellation
    # was deliberately requested by the user.
    pass


class ExecutionWorker(QObject):

    # ------------------------------------------------------------------
    # SIGNALS: WORKER COMMUNICATION
    # ------------------------------------------------------------------
    # progress sends the current batch number and total processed rows.
    progress = Signal(int, int)

    # completed sends execution statistics after successful processing.
    completed = Signal(object)

    # cancelled sends statistics after a user-requested cancellation.
    cancelled = Signal(object)

    # failed sends execution statistics including the error message.
    failed = Signal(object)

    # finished tells QThread that worker processing has ended.
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
        # SECTION 2: STORE EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        # Store copies so background processing does not depend directly
        # on GUI widgets or dictionaries that may later change.
        self.connection_config = connection_config.copy()
        self.source_config = source_config.copy()
        self.rules = rules.copy()
        self.target_config = target_config.copy()
        self.included_columns = included_columns.copy()
        self.batch_size = batch_size

    def check_cancellation(self):
        # ------------------------------------------------------------------
        # SECTION 3: CHECK FOR CANCELLATION REQUEST
        # ------------------------------------------------------------------
        # requestInterruption() does not terminate a QThread automatically.
        #
        # The running worker checks isInterruptionRequested() and raises
        # ExecutionCancelled when it reaches a safe checkpoint.
        current_thread = QThread.currentThread()

        if current_thread.isInterruptionRequested():
            raise ExecutionCancelled()

    @Slot()
    def run(self):
        # ------------------------------------------------------------------
        # SECTION 4: READ EXECUTION SETTINGS
        # ------------------------------------------------------------------
        source_schema = self.source_config["source_schema"]
        source_table = self.source_config["source_table"]

        target_schema = self.target_config["target_schema"]
        target_table = self.target_config["target_table"]

        connection = None
        batch_number = 0
        total_rows = 0

        # Record when actual background execution begins.
        started_at = datetime.now()

        try:
            # ------------------------------------------------------------------
            # SECTION 5: CONNECT TO ORACLE
            # ------------------------------------------------------------------
            # The worker creates its own Oracle connection inside QThread.
            connection = connect_to_oracle(
                self.connection_config
            )

            # Check whether cancellation was requested while connecting.
            self.check_cancellation()

            # ------------------------------------------------------------------
            # SECTION 6: PROCESS SOURCE DATA IN BATCHES
            # ------------------------------------------------------------------
            # Only one source batch is retrieved at a time so large tables
            # do not need to be loaded completely into memory.
            for batch in read_rows_in_batches(
                connection,
                source_schema,
                source_table,
                batch_size=self.batch_size
            ):
                # --------------------------------------------------------------
                # SECTION 7: CHECK CANCELLATION BEFORE BATCH
                # --------------------------------------------------------------
                # This prevents another batch from beginning after cancellation
                # has already been requested.
                self.check_cancellation()

                batch_number += 1

                # --------------------------------------------------------------
                # SECTION 8: TRANSFORM COMPLETE BATCH
                # --------------------------------------------------------------
                transformed_batch = []

                for row in batch:
                    # Check regularly during transformation so cancellation
                    # does not have to wait for the entire batch to transform.
                    self.check_cancellation()

                    transformed_row = transform_row(
                        row,
                        self.rules
                    )

                    transformed_batch.append(
                        transformed_row
                    )

                # --------------------------------------------------------------
                # SECTION 9: CHECK BEFORE DATABASE INSERT
                # --------------------------------------------------------------
                # Do not start executemany() when cancellation was requested
                # during batch transformation.
                self.check_cancellation()

                # --------------------------------------------------------------
                # SECTION 10: INSERT COMPLETE BATCH
                # --------------------------------------------------------------
                # insert_rows_batch() uses cursor.executemany().
                #
                # It deliberately does NOT commit.
                insert_rows_batch(
                    connection,
                    target_schema,
                    target_table,
                    transformed_batch,
                    self.included_columns
                )

                # Count rows after the complete batch inserts successfully.
                total_rows += len(transformed_batch)

                # --------------------------------------------------------------
                # SECTION 11: CHECK AFTER DATABASE INSERT
                # --------------------------------------------------------------
                # If cancellation was requested while executemany() was
                # executing, detect it immediately after Oracle returns.
                #
                # The inserted rows are still uncommitted and can therefore
                # be rolled back safely.
                self.check_cancellation()

                # Notify the GUI after each successful batch.
                self.progress.emit(
                    batch_number,
                    total_rows
                )

            # ------------------------------------------------------------------
            # SECTION 12: FINAL CANCELLATION CHECK
            # ------------------------------------------------------------------
            # Protect the small window between the final batch and commit.
            self.check_cancellation()

            # ------------------------------------------------------------------
            # SECTION 13: COMMIT COMPLETE EXECUTION
            # ------------------------------------------------------------------
            # Commit only after every source batch succeeds and no
            # cancellation request remains pending.
            connection.commit()

            logger.info(
                "Anonymization transaction committed successfully | "
                "Source=%s.%s | Target=%s.%s | Rows=%s | Batches=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                total_rows,
                batch_number
            )

            completed_at = datetime.now()

            # ------------------------------------------------------------------
            # SECTION 14: BUILD SUCCESS STATISTICS
            # ------------------------------------------------------------------
            execution_stats = {
                "status": "SUCCESS",
                "rows_processed": total_rows,
                "batches_processed": batch_number,
                "batch_size": self.batch_size,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": (
                    completed_at - started_at
                ).total_seconds(),
                "error": None
            }

            self.completed.emit(
                execution_stats
            )

        except ExecutionCancelled:
            # ------------------------------------------------------------------
            # SECTION 15: HANDLE USER-REQUESTED CANCELLATION
            # ------------------------------------------------------------------
            # Cancellation is not considered a technical application failure.
            #
            # Roll back all DML performed by this worker because the final
            # successful commit was never reached.
            if connection is not None:
                try:
                    connection.rollback()

                    logger.warning(
                        "Anonymization execution cancelled and transaction "
                        "rolled back | Source=%s.%s | Target=%s.%s | "
                        "RowsBeforeRollback=%s | BatchesBeforeCancellation=%s",
                        source_schema,
                        source_table,
                        target_schema,
                        target_table,
                        total_rows,
                        batch_number
                    )

                except Exception as rollback_error:
                    # ----------------------------------------------------------
                    # SECTION 16: HANDLE CANCELLATION ROLLBACK FAILURE
                    # ----------------------------------------------------------
                    logger.exception(
                        "Rollback failed after execution cancellation | "
                        "Source=%s.%s | Target=%s.%s | Error=%s",
                        source_schema,
                        source_table,
                        target_schema,
                        target_table,
                        rollback_error
                    )

            completed_at = datetime.now()

            # ------------------------------------------------------------------
            # SECTION 17: BUILD CANCELLATION STATISTICS
            # ------------------------------------------------------------------
            execution_stats = {
                "status": "CANCELLED",
                "rows_processed": total_rows,
                "batches_processed": batch_number,
                "batch_size": self.batch_size,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": (
                    completed_at - started_at
                ).total_seconds(),
                "error": None
            }

            self.cancelled.emit(
                execution_stats
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 18: HANDLE WORKER FAILURE
            # ------------------------------------------------------------------
            logger.exception(
                "Anonymization worker failed | "
                "Source=%s.%s | Target=%s.%s | "
                "RowsBeforeRollback=%s | BatchesBeforeRollback=%s | Error=%s",
                source_schema,
                source_table,
                target_schema,
                target_table,
                total_rows,
                batch_number,
                error
            )

            # ------------------------------------------------------------------
            # SECTION 19: ROLLBACK FAILED EXECUTION
            # ------------------------------------------------------------------
            if connection is not None:
                try:
                    connection.rollback()

                    logger.warning(
                        "Anonymization transaction rolled back | "
                        "Source=%s.%s | Target=%s.%s | "
                        "RowsRolledBack=%s | BatchesBeforeFailure=%s",
                        source_schema,
                        source_table,
                        target_schema,
                        target_table,
                        total_rows,
                        batch_number
                    )

                except Exception as rollback_error:
                    # ----------------------------------------------------------
                    # SECTION 20: HANDLE ROLLBACK FAILURE
                    # ----------------------------------------------------------
                    logger.exception(
                        "Transaction rollback failed | "
                        "Source=%s.%s | Target=%s.%s | Error=%s",
                        source_schema,
                        source_table,
                        target_schema,
                        target_table,
                        rollback_error
                    )

            completed_at = datetime.now()

            # ------------------------------------------------------------------
            # SECTION 21: BUILD FAILURE STATISTICS
            # ------------------------------------------------------------------
            execution_stats = {
                "status": "FAILED",
                "rows_processed": total_rows,
                "batches_processed": batch_number,
                "batch_size": self.batch_size,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_seconds": (
                    completed_at - started_at
                ).total_seconds(),
                "error": str(error)
            }

            self.failed.emit(
                execution_stats
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 22: CLOSE DATABASE CONNECTION
            # ------------------------------------------------------------------
            if connection is not None:
                try:
                    connection.close()

                except Exception as close_error:
                    logger.warning(
                        "Worker Oracle connection close failed | "
                        "Source=%s.%s | Target=%s.%s | Error=%s",
                        source_schema,
                        source_table,
                        target_schema,
                        target_table,
                        close_error
                    )

            # ------------------------------------------------------------------
            # SECTION 23: NOTIFY THREAD THAT WORK IS FINISHED
            # ------------------------------------------------------------------
            self.finished.emit()