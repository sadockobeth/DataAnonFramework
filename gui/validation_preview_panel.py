"""
Module: validation_preview_panel.py

Purpose:
Validates the anonymization configuration and displays a read-only
preview of original and anonymized values before execution.

Main responsibilities:
- Receive GUI database connection and anonymization configuration.
- Validate the configuration using configuration_validator.py.
- Connect to Oracle using the tested GUI connection configuration.
- Read a small sample of source rows without modifying Oracle data.
- Apply configured anonymization rules to preview rows.
- Display original and anonymized values for columns being anonymized.
- Display unchanged columns only once to reduce unnecessary preview width.
- Exclude columns that will not appear in the target table.
- Record preview validation, success, and failure events in the technical log.
- Clear previous preview results when starting a new session.

Sensitive source and anonymized row values are intentionally not written
to the technical log.

This module does not create target tables, insert data, commit transactions,
or perform full anonymization execution.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView
)

from database.oracle_connection import connect_to_oracle
from database.data_reader import read_rows_in_batches
from anonymization.row_transformation_manager import transform_row
from validation.configuration_validator import validate_configuration
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
# Use the shared application technical logger.
#
# Preview row values are never written to this logger because they may
# contain sensitive information.
logger = get_logger()


class ValidationPreviewPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CREATE PREVIEW BUTTON
        # ------------------------------------------------------------------
        # Clicking this button starts configuration validation followed
        # by a read-only anonymization preview.
        self.preview_button = QPushButton("Validate and Preview")

        # ------------------------------------------------------------------
        # SECTION 3: CREATE PREVIEW TABLE
        # ------------------------------------------------------------------
        # QTableWidget displays original and anonymized sample values.
        self.preview_table = QTableWidget()

        # Keep enough vertical space to display several preview rows.
        self.preview_table.setMinimumHeight(150)

        # Preview results are informational and should not be edited.
        self.preview_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # QLabel displays validation, preview success, and error messages.
        self.status_label = QLabel("Preview not yet generated.")

        # ------------------------------------------------------------------
        # SECTION 5: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout places preview controls and results vertically.
        layout = QVBoxLayout()

        layout.addWidget(self.preview_button)
        layout.addWidget(QLabel("Anonymization Preview:"))
        layout.addWidget(self.preview_table)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def run_preview(
        self,
        connection_config,
        source_config,
        rules,
        target_config
    ):
        # ------------------------------------------------------------------
        # SECTION 6: VALIDATE GUI DATABASE CONNECTION
        # ------------------------------------------------------------------
        # Preview requires a connection that was successfully tested in
        # DatabaseConnectionPanel.
        if connection_config is None:
            logger.warning(
                "Preview stopped because no tested GUI database connection "
                "was available."
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Preview stopped: Test the database connection first."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 7: VALIDATE ANONYMIZATION CONFIGURATION
        # ------------------------------------------------------------------
        # Preview and execution use the same shared validation rules.
        validation_error = validate_configuration(
            source_config,
            rules,
            target_config
        )

        if validation_error:
            logger.warning(
                "Preview validation failed | Source=%s.%s | Reason=%s",
                source_config.get("source_schema", ""),
                source_config.get("source_table", ""),
                validation_error
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Preview stopped: {validation_error}"
            )

            return

        # ------------------------------------------------------------------
        # SECTION 8: READ PREVIEW CONFIGURATION
        # ------------------------------------------------------------------
        source_schema = source_config["source_schema"]
        source_table = source_config["source_table"]

        excluded_columns = target_config["excluded_columns"]

        # Only columns that will exist in the target table should appear
        # in the preview.
        included_columns = [
            column["column_name"]
            for column in source_config["table_columns"]
            if column["column_name"] not in excluded_columns
        ]

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 9: START PREVIEW
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")
            self.status_label.setText("Generating preview...")

            # Remove any previous preview contents.
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)

            # Open a short-lived Oracle connection using the tested GUI
            # connection configuration.
            connection = connect_to_oracle(
                connection_config
            )

            # ------------------------------------------------------------------
            # SECTION 10: READ FIRST SOURCE BATCH
            # ------------------------------------------------------------------
            # Preview reads at most five rows.
            preview_rows = []

            for batch in read_rows_in_batches(
                connection,
                source_schema,
                source_table,
                batch_size=5
            ):
                preview_rows = batch
                break

            # ------------------------------------------------------------------
            # SECTION 11: HANDLE EMPTY SOURCE TABLE
            # ------------------------------------------------------------------
            if not preview_rows:
                logger.warning(
                    "Preview returned no rows | Source=%s.%s",
                    source_schema,
                    source_table
                )

                self.preview_table.clear()
                self.preview_table.setRowCount(0)
                self.preview_table.setColumnCount(0)

                self.status_label.setStyleSheet("")
                self.status_label.setText(
                    f"No rows found in {source_schema}.{source_table}."
                )

                return

            # ------------------------------------------------------------------
            # SECTION 12: TRANSFORM PREVIEW ROWS
            # ------------------------------------------------------------------
            # Store original and transformed rows only in application memory.
            # Sensitive preview values are intentionally not logged.
            transformed_rows = []

            for row in preview_rows:
                transformed_rows.append(
                    transform_row(
                        row,
                        rules
                    )
                )

            # ------------------------------------------------------------------
            # SECTION 13: CONFIGURE PREVIEW TABLE
            # ------------------------------------------------------------------
            # Columns with anonymization rules are displayed twice:
            #
            # COLUMN - ORIGINAL
            # COLUMN - ANONYMIZED
            #
            # Columns without anonymization rules are displayed only once
            # because their values remain unchanged.
            #
            # Excluded columns do not appear in the preview at all.
            headers = []

            for column_name in included_columns:
                if column_name in rules:
                    headers.append(
                        f"{column_name} - ORIGINAL"
                    )

                    headers.append(
                        f"{column_name} - ANONYMIZED"
                    )

                else:
                    headers.append(
                        column_name
                    )

            self.preview_table.setColumnCount(
                len(headers)
            )

            self.preview_table.setHorizontalHeaderLabels(
                headers
            )

            self.preview_table.setRowCount(
                len(preview_rows)
            )

            # ------------------------------------------------------------------
            # SECTION 14: DISPLAY PREVIEW VALUES
            # ------------------------------------------------------------------
            # Anonymized columns show both the original and protected values.
            #
            # Unchanged columns show only their original value once.
            for row_number, original_row in enumerate(preview_rows):
                transformed_row = transformed_rows[row_number]

                table_column = 0

                for column_name in included_columns:
                    original_value = original_row.get(
                        column_name
                    )

                    original_text = (
                        ""
                        if original_value is None
                        else str(original_value)
                    )

                    # ----------------------------------------------------------
                    # COLUMN HAS AN ANONYMIZATION RULE
                    # ----------------------------------------------------------
                    if column_name in rules:
                        anonymized_value = transformed_row.get(
                            column_name
                        )

                        anonymized_text = (
                            ""
                            if anonymized_value is None
                            else str(anonymized_value)
                        )

                        # Display the original value.
                        self.preview_table.setItem(
                            row_number,
                            table_column,
                            QTableWidgetItem(
                                original_text
                            )
                        )

                        # Display the anonymized value beside it.
                        self.preview_table.setItem(
                            row_number,
                            table_column + 1,
                            QTableWidgetItem(
                                anonymized_text
                            )
                        )

                        # Two preview columns were used.
                        table_column += 2

                    # ----------------------------------------------------------
                    # COLUMN IS NOT ANONYMIZED
                    # ----------------------------------------------------------
                    else:
                        # The value remains unchanged, therefore display
                        # the source value only once.
                        self.preview_table.setItem(
                            row_number,
                            table_column,
                            QTableWidgetItem(
                                original_text
                            )
                        )

                        # Only one preview column was used.
                        table_column += 1

            # Resize columns according to their displayed contents.
            self.preview_table.resizeColumnsToContents()

            # ------------------------------------------------------------------
            # SECTION 15: REPORT PREVIEW SUCCESS
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")

            self.status_label.setText(
                f"Preview generated successfully using "
                f"{len(preview_rows)} row(s)."
            )

            # Log operational information only.
            # Sensitive row values are intentionally excluded.
            logger.info(
                "Preview generated successfully | Source=%s.%s | "
                "Rows=%s | Rules=%s | ExcludedColumns=%s",
                source_schema,
                source_table,
                len(preview_rows),
                len(rules),
                len(excluded_columns)
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 16: HANDLE PREVIEW FAILURE
            # ------------------------------------------------------------------
            # Record the technical error and traceback but never log
            # source or anonymized row contents.
            logger.exception(
                "Preview failed | Source=%s.%s | Error=%s",
                source_schema,
                source_table,
                error
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Preview failed: {error}"
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 17: CLOSE DATABASE CONNECTION
            # ------------------------------------------------------------------
            # Preview is read-only and uses a short-lived Oracle connection.
            if connection is not None:
                connection.close()

    def clear_preview(self):
        # ------------------------------------------------------------------
        # SECTION 18: CLEAR PREVIEW PANEL
        # ------------------------------------------------------------------
        # Remove previous preview rows, headers, and status information.
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Preview not yet generated."
        )