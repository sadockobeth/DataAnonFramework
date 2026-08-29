"""
Module: validation_preview_panel.py

Purpose:
Validates the current anonymization configuration and displays a safe
sample preview before full anonymization execution.

Main responsibilities:
- Validate the current source, rule, and target configuration.
- Read a small sample of source rows from Oracle.
- Apply the configured anonymization rules to the sample rows.
- Display original and anonymized values side by side for protected columns.
- Display unchanged columns only once.
- Omit columns excluded from the target table.
- Format Decimal values clearly for preview display.
- Confirm that preview operations do not write data to Oracle.
- Clear preview results when starting a new application session.
- Record preview activity without logging sensitive row values.

This module does not create target tables, insert anonymized rows,
commit database transactions, or modify source data.
"""

from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView
)

from database.oracle_connection import connect_to_oracle
from database.data_reader import read_rows_in_batches
from anonymization.row_transformation_manager import transform_row
from validation.configuration_validator import validate_configuration
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
logger = get_logger()


class ValidationPreviewPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CREATE PREVIEW INFORMATION LABEL
        # ------------------------------------------------------------------
        self.description_label = QLabel(
            "Validate the configuration and review a small sample before "
            "executing anonymization."
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE PREVIEW BUTTON
        # ------------------------------------------------------------------
        # Keep this exact button name because MainWindow already connects
        # directly to preview_button.clicked.
        self.preview_button = QPushButton(
            "Validate and Preview"
        )

        self.preview_button.setObjectName(
            "primaryButton"
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE PREVIEW TABLE
        # ------------------------------------------------------------------
        self.preview_table = QTableWidget()

        # Preview values are informational only.
        self.preview_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.preview_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.preview_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.preview_table.setAlternatingRowColors(
            True
        )

        self.preview_table.verticalHeader().setVisible(
            False
        )

        # Keep the preview compact but large enough to compare several rows.
        self.preview_table.setMinimumHeight(
            170
        )

        # Column widths should follow the displayed values while still
        # allowing the user to resize columns manually.
        header = self.preview_table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setStretchLastSection(
            True
        )

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Preview has not been generated."
        )

        # ------------------------------------------------------------------
        # SECTION 6: CREATE ACTION ROW
        # ------------------------------------------------------------------
        action_layout = QHBoxLayout()

        action_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        action_layout.addWidget(
            self.description_label
        )

        action_layout.addStretch()

        action_layout.addWidget(
            self.preview_button
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's numbered QGroupBox already supplies outer spacing.
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            6
        )

        layout.addLayout(
            action_layout
        )

        layout.addWidget(
            QLabel("Preview Results")
        )

        layout.addWidget(
            self.preview_table
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(
            layout
        )

    def run_preview(
        self,
        connection_config,
        source_config,
        rules,
        target_config
    ):
        # ------------------------------------------------------------------
        # SECTION 8: CLEAR PREVIOUS PREVIEW RESULT
        # ------------------------------------------------------------------
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)

        self.status_label.setStyleSheet("")

        # ------------------------------------------------------------------
        # SECTION 9: VALIDATE DATABASE CONNECTION
        # ------------------------------------------------------------------
        if connection_config is None:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Validation failed: Test the database connection first."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 10: VALIDATE COMPLETE CONFIGURATION
        # ------------------------------------------------------------------
        # The shared validator checks:
        #
        # - source schema and table
        # - source metadata
        # - anonymization rules
        # - datatype compatibility
        # - target schema and table
        # - exclusions
        # - rule/exclusion conflicts
        validation_error = validate_configuration(
            source_config,
            rules,
            target_config
        )

        if validation_error:
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Validation failed: {validation_error}"
            )

            logger.warning(
                "Preview validation failed because the configuration "
                "was invalid."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 11: READ SOURCE CONFIGURATION
        # ------------------------------------------------------------------
        source_schema = source_config["source_schema"]
        source_table = source_config["source_table"]
        table_columns = source_config["table_columns"]

        excluded_columns = target_config[
            "excluded_columns"
        ]

        # ------------------------------------------------------------------
        # SECTION 12: DETERMINE TARGET COLUMNS
        # ------------------------------------------------------------------
        # Preview only columns that will exist in the OUT_PLACE target.
        source_columns = [
            column["column_name"]
            for column in table_columns
        ]

        included_columns = [
            column_name
            for column_name in source_columns
            if column_name not in excluded_columns
        ]

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 13: START PREVIEW
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")

            self.status_label.setText(
                "Validating configuration and loading preview..."
            )

            logger.info(
                "Preview started | Source=%s.%s | Rules=%s | "
                "ExcludedColumns=%s",
                source_schema,
                source_table,
                len(rules),
                len(excluded_columns)
            )

            # ------------------------------------------------------------------
            # SECTION 14: CONNECT TO ORACLE
            # ------------------------------------------------------------------
            connection = connect_to_oracle(
                connection_config
            )

            # ------------------------------------------------------------------
            # SECTION 15: READ FIRST FIVE SOURCE ROWS
            # ------------------------------------------------------------------
            # read_rows_in_batches() is reused rather than creating separate
            # preview-specific database-reading logic.
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
            # SECTION 16: HANDLE EMPTY SOURCE TABLE
            # ------------------------------------------------------------------
            if not preview_rows:
                self.preview_table.clear()
                self.preview_table.setRowCount(0)
                self.preview_table.setColumnCount(0)

                self.status_label.setStyleSheet(
                    "color: green; font-weight: bold;"
                )

                self.status_label.setText(
                    "✓ Configuration is valid, but the source table "
                    "contains no rows to preview."
                )

                logger.info(
                    "Preview validation successful, but no source rows "
                    "were available."
                )

                return

            # ------------------------------------------------------------------
            # SECTION 17: TRANSFORM PREVIEW ROWS
            # ------------------------------------------------------------------
            transformed_rows = []

            for row in preview_rows:
                transformed_rows.append(
                    transform_row(
                        row,
                        rules
                    )
                )

            # ------------------------------------------------------------------
            # SECTION 18: BUILD PREVIEW COLUMN STRUCTURE
            # ------------------------------------------------------------------
            # Protected columns receive two displayed columns:
            #
            # FULL_NAME - ORIGINAL
            # FULL_NAME - ANONYMIZED
            #
            # Unchanged columns appear once.
            #
            # Excluded columns do not appear at all.
            preview_columns = []

            for column_name in included_columns:

                if column_name in rules:
                    preview_columns.append({
                        "header": f"{column_name} - ORIGINAL",
                        "column_name": column_name,
                        "value_type": "original"
                    })

                    preview_columns.append({
                        "header": f"{column_name} - ANONYMIZED",
                        "column_name": column_name,
                        "value_type": "anonymized"
                    })

                else:
                    preview_columns.append({
                        "header": column_name,
                        "column_name": column_name,
                        "value_type": "unchanged"
                    })

            # ------------------------------------------------------------------
            # SECTION 19: CONFIGURE PREVIEW TABLE
            # ------------------------------------------------------------------
            self.preview_table.setRowCount(
                len(preview_rows)
            )

            self.preview_table.setColumnCount(
                len(preview_columns)
            )

            headers = [
                column["header"]
                for column in preview_columns
            ]

            self.preview_table.setHorizontalHeaderLabels(
                headers
            )

            # ------------------------------------------------------------------
            # SECTION 20: DISPLAY PREVIEW VALUES
            # ------------------------------------------------------------------
            for row_index, original_row in enumerate(
                preview_rows
            ):
                anonymized_row = transformed_rows[
                    row_index
                ]

                for column_index, preview_column in enumerate(
                    preview_columns
                ):
                    column_name = preview_column[
                        "column_name"
                    ]

                    value_type = preview_column[
                        "value_type"
                    ]

                    if value_type == "original":
                        value = original_row.get(
                            column_name
                        )

                    elif value_type == "anonymized":
                        value = anonymized_row.get(
                            column_name
                        )

                    else:
                        value = original_row.get(
                            column_name
                        )

                    item = QTableWidgetItem(
                        self.format_preview_value(
                            value
                        )
                    )

                    self.preview_table.setItem(
                        row_index,
                        column_index,
                        item
                    )

            # ------------------------------------------------------------------
            # SECTION 21: REPORT SUCCESS
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet(
                "color: green; font-weight: bold;"
            )

            self.status_label.setText(
                f"✓ Validation successful. Previewing "
                f"{len(preview_rows)} row(s). "
                f"No data has been written to the Databse yet."
            )

            logger.info(
                "Preview completed successfully | Source=%s.%s | Rows=%s",
                source_schema,
                source_table,
                len(preview_rows)
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 22: HANDLE PREVIEW FAILURE
            # ------------------------------------------------------------------
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Preview failed: {error}"
            )

            # Do not log source row values because they may contain
            # confidential or sensitive information.
            logger.exception(
                "Preview failed | Source=%s.%s",
                source_schema,
                source_table
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 23: CLOSE PREVIEW CONNECTION
            # ------------------------------------------------------------------
            if connection is not None:
                connection.close()

    def format_preview_value(
        self,
        value
    ):
        # ------------------------------------------------------------------
        # SECTION 24: FORMAT PREVIEW VALUE
        # ------------------------------------------------------------------
        if value is None:
            return ""

        # Oracle NUMBER values may arrive as Decimal.
        #
        # format(value, "f") prevents values such as:
        #
        # Decimal("4E+6")
        #
        # from appearing as:
        #
        # 4E+6
        #
        # and instead displays:
        #
        # 4000000
        if isinstance(
            value,
            Decimal
        ):
            return format(
                value,
                "f"
            )

        return str(
            value
        )

    def clear_preview(self):
        # ------------------------------------------------------------------
        # SECTION 25: CLEAR PREVIEW PANEL
        # ------------------------------------------------------------------
        self.preview_table.clear()

        self.preview_table.setRowCount(
            0
        )

        self.preview_table.setColumnCount(
            0
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Preview has not been generated."
        )