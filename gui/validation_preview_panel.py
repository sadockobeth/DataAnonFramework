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
- Format Decimal values in normal numeric form instead of scientific notation.
- Record preview validation, success, and failure events in the technical log.
- Clear previous preview results when starting a new session.

Sensitive source and anonymized row values are intentionally not written
to the technical log.

This module does not create target tables, insert data, commit transactions,
or perform full anonymization execution.
"""

from decimal import Decimal

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

    def format_preview_value(self, value):
        # ------------------------------------------------------------------
        # SECTION 6: FORMAT VALUE FOR PREVIEW DISPLAY
        # ------------------------------------------------------------------
        # Decimal values may otherwise appear in scientific notation.
        #
        # Example:
        #
        # Decimal("4E+6")
        #
        # str(value)     -> 4E+6
        # format(...,"f") -> 4000000
        #
        # This affects only the GUI display. The actual numeric value used
        # during execution remains unchanged.
        if value is None:
            return ""

        if isinstance(value, Decimal):
            return format(value, "f")

        return str(value)

    def run_preview(
        self,
        connection_config,
        source_config,
        rules,
        target_config
    ):
        # ------------------------------------------------------------------
        # SECTION 7: VALIDATE GUI DATABASE CONNECTION
        # ------------------------------------------------------------------
        # Preview requires a successfully tested database connection.
        if connection_config is None:
            logger.warning(
                "Preview stopped because no tested GUI database connection was available."
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Preview stopped: Test the database connection first."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 8: VALIDATE ANONYMIZATION CONFIGURATION
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
        # SECTION 9: READ PREVIEW CONFIGURATION
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
            # SECTION 10: START PREVIEW
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")
            self.status_label.setText("Generating preview...")

            # Remove any previous preview contents.
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)

            # Open a short-lived Oracle connection.
            connection = connect_to_oracle(
                connection_config
            )

            # ------------------------------------------------------------------
            # SECTION 11: READ FIRST SOURCE BATCH
            # ------------------------------------------------------------------
            # Preview reads at most five source rows.
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
            # SECTION 12: HANDLE EMPTY SOURCE TABLE
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
            # SECTION 13: TRANSFORM PREVIEW ROWS
            # ------------------------------------------------------------------
            # Original and transformed row values remain only in memory.
            transformed_rows = []

            for row in preview_rows:
                transformed_rows.append(
                    transform_row(
                        row,
                        rules
                    )
                )

            # ------------------------------------------------------------------
            # SECTION 14: CONFIGURE PREVIEW TABLE
            # ------------------------------------------------------------------
            # Columns with anonymization rules appear twice:
            #
            # COLUMN - ORIGINAL
            # COLUMN - ANONYMIZED
            #
            # Columns without anonymization rules appear only once.
            #
            # Excluded columns do not appear.
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
            # SECTION 15: DISPLAY PREVIEW VALUES
            # ------------------------------------------------------------------
            # Anonymized columns show original and anonymized values.
            #
            # Unchanged columns show their value only once.
            for row_number, original_row in enumerate(preview_rows):
                transformed_row = transformed_rows[row_number]
                table_column = 0

                for column_name in included_columns:
                    original_value = original_row.get(
                        column_name
                    )

                    original_text = self.format_preview_value(
                        original_value
                    )

                    # ----------------------------------------------------------
                    # COLUMN HAS AN ANONYMIZATION RULE
                    # ----------------------------------------------------------
                    if column_name in rules:
                        anonymized_value = transformed_row.get(
                            column_name
                        )

                        anonymized_text = self.format_preview_value(
                            anonymized_value
                        )

                        # Display original value.
                        self.preview_table.setItem(
                            row_number,
                            table_column,
                            QTableWidgetItem(
                                original_text
                            )
                        )

                        # Display anonymized value.
                        self.preview_table.setItem(
                            row_number,
                            table_column + 1,
                            QTableWidgetItem(
                                anonymized_text
                            )
                        )

                        table_column += 2

                    # ----------------------------------------------------------
                    # COLUMN IS NOT ANONYMIZED
                    # ----------------------------------------------------------
                    else:
                        # No anonymization rule exists, therefore displaying
                        # the value once is sufficient.
                        self.preview_table.setItem(
                            row_number,
                            table_column,
                            QTableWidgetItem(
                                original_text
                            )
                        )

                        table_column += 1

            # Resize columns according to displayed contents.
            self.preview_table.resizeColumnsToContents()

            # ------------------------------------------------------------------
            # SECTION 16: REPORT PREVIEW SUCCESS
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")

            self.status_label.setText(
                f"Preview generated successfully using "
                f"{len(preview_rows)} row(s)."
            )

            # Log operational information only.
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
            # SECTION 17: HANDLE PREVIEW FAILURE
            # ------------------------------------------------------------------
            # Record the error and traceback without logging preview data.
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
            # SECTION 18: CLOSE DATABASE CONNECTION
            # ------------------------------------------------------------------
            # Preview uses a short-lived read-only connection.
            if connection is not None:
                connection.close()

    def clear_preview(self):
        # ------------------------------------------------------------------
        # SECTION 19: CLEAR PREVIEW PANEL
        # ------------------------------------------------------------------
        # Remove previous preview rows, headers, and status information.
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)

        self.status_label.setStyleSheet("")
        self.status_label.setText(
            "Preview not yet generated."
        )