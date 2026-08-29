"""
Module: source_table_panel.py

Purpose:
Handles source Oracle table selection and source table metadata in the GUI.

Main responsibilities:
- Accept source schema and table names from the user.
- Receive a successfully tested GUI database connection configuration.
- Use the GUI connection configuration when retrieving source metadata.
- Retrieve source table metadata using database_metadata.py.
- Display available source columns and datatypes.
- Return the currently selected source column to other GUI components.
- Return metadata for the currently selected source column.
- Return the current source-table configuration.
- Notify other GUI components when source columns are successfully loaded.
- Clear the current source configuration so a new session can start.
- Record important source-metadata events and failures in the technical log.

This module does not test database connections and does not perform anonymization.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget
)

from database.oracle_connection import connect_to_oracle
from database.database_metadata import get_table_columns
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
# Use the shared DataAnonFramework logger for source metadata events.
logger = get_logger()


class SourceTablePanel(QWidget):

    # ------------------------------------------------------------------
    # SIGNAL: SOURCE COLUMNS LOADED
    # ------------------------------------------------------------------
    # The signal announces that source metadata has been loaded.
    # It sends the source table name and list of column names.
    columns_loaded = Signal(str, object)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CREATE SOURCE INPUT FIELDS
        # ------------------------------------------------------------------
        # QLineEdit provides text boxes for entering the Oracle schema
        # and source table.
        self.source_schema_input = QLineEdit()
        self.source_table_input = QLineEdit()

        # ------------------------------------------------------------------
        # SECTION 3: CREATE SOURCE ACTION BUTTON
        # ------------------------------------------------------------------
        # This button retrieves metadata for the entered source table.
        self.load_columns_button = QPushButton("Load Columns")

        # ------------------------------------------------------------------
        # SECTION 4: CREATE COLUMN LIST
        # ------------------------------------------------------------------
        # QListWidget displays Oracle columns returned from the database.
        self.column_list = QListWidget()

        # Keep enough vertical space to display at least five source columns.
        self.column_list.setMinimumHeight(150)

        # Reduce the list font size so more column information can be shown.
        column_list_font = self.column_list.font()
        column_list_font.setPointSize(8)
        self.column_list.setFont(column_list_font)

        # Store complete Oracle column metadata for later use.
        self.table_columns = []

        # Store the successfully tested GUI database configuration.
        self.connection_config = None

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # QLabel displays loading, validation, and source metadata messages.
        self.status_label = QLabel("Status: Database connection not ready")

        # ------------------------------------------------------------------
        # SECTION 6: CREATE SOURCE FORM LAYOUT
        # ------------------------------------------------------------------
        # QFormLayout arranges labels beside their corresponding inputs.
        form_layout = QFormLayout()
        form_layout.addRow("Source Schema:", self.source_schema_input)
        form_layout.addRow("Source Table:", self.source_table_input)

        # ------------------------------------------------------------------
        # SECTION 7: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout arranges the source-table controls vertically.
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.load_columns_button)
        layout.addWidget(QLabel("Available Columns:"))
        layout.addWidget(self.column_list)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 8: CONNECT BUTTON TO FUNCTION
        # ------------------------------------------------------------------
        # clicked.connect() tells Qt which method to call after a click.
        self.load_columns_button.clicked.connect(self.load_columns)

    def set_connection_config(self, connection_config):
        # ------------------------------------------------------------------
        # SECTION 9: RECEIVE DATABASE CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # MainWindow passes the successfully tested GUI connection
        # configuration received from DatabaseConnectionPanel.
        self.connection_config = connection_config

        self.status_label.setStyleSheet("")
        self.status_label.setText("Status: Database connection ready.")

    def load_columns(self):
        # ------------------------------------------------------------------
        # SECTION 10: READ SOURCE SCHEMA AND TABLE
        # ------------------------------------------------------------------
        source_schema = self.source_schema_input.text().strip().upper()
        source_table = self.source_table_input.text().strip().upper()

        # ------------------------------------------------------------------
        # SECTION 11: VALIDATE REQUIRED INPUT
        # ------------------------------------------------------------------
        if not source_schema:
            logger.warning("Source metadata loading stopped because source schema was not provided.")

            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText("Status: Enter source schema.")
            return

        if not source_table:
            logger.warning("Source metadata loading stopped because source table was not provided.")

            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText("Status: Enter source table.")
            return

        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE GUI DATABASE CONNECTION
        # ------------------------------------------------------------------
        # Source metadata can only be loaded after the user has successfully
        # tested the database connection.
        if self.connection_config is None:
            logger.warning(
                "Source metadata loading stopped because no tested GUI database connection was available."
            )

            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText("Status: Test the database connection first.")
            return

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 13: RETRIEVE ORACLE TABLE METADATA
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")
            self.status_label.setText("Status: Loading columns...")

            # Open an Oracle connection using the already tested GUI settings.
            connection = connect_to_oracle(self.connection_config)

            # Retrieve source table column metadata.
            self.table_columns = get_table_columns(
                connection,
                source_schema,
                source_table
            )

            # ------------------------------------------------------------------
            # SECTION 14: HANDLE TABLE NOT FOUND
            # ------------------------------------------------------------------
            # No returned metadata may mean the table does not exist or is
            # not accessible to the connected Oracle user.
            if not self.table_columns:
                self.column_list.clear()

                logger.warning(
                    "No metadata returned for source table %s.%s.",
                    source_schema,
                    source_table
                )

                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText(
                    f"Status: Table {source_schema}.{source_table} not found."
                )
                return

            # ------------------------------------------------------------------
            # SECTION 15: DISPLAY SOURCE COLUMNS
            # ------------------------------------------------------------------
            # Clear previously displayed columns before loading the new table.
            self.column_list.clear()

            for column in self.table_columns:
                self.column_list.addItem(
                    f'{column["column_name"]} ({column["data_type"]})'
                )

            self.status_label.setStyleSheet("")
            self.status_label.setText(
                f"Status: {len(self.table_columns)} columns loaded from "
                f"{source_schema}.{source_table}."
            )

            # ------------------------------------------------------------------
            # SECTION 16: LOG SUCCESSFUL METADATA LOADING
            # ------------------------------------------------------------------
            logger.info(
                "Source metadata loaded successfully | Table=%s.%s | Columns=%s",
                source_schema,
                source_table,
                len(self.table_columns)
            )

            # ------------------------------------------------------------------
            # SECTION 17: NOTIFY OTHER GUI COMPONENTS
            # ------------------------------------------------------------------
            column_names = [
                column["column_name"]
                for column in self.table_columns
            ]

            self.columns_loaded.emit(
                source_table,
                column_names
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 18: HANDLE METADATA LOADING FAILURE
            # ------------------------------------------------------------------
            # Record both the error and traceback in the technical log.
            logger.exception(
                "Failed to load source metadata | Table=%s.%s | Error=%s",
                source_schema,
                source_table,
                error
            )

            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText(f"Status: Error - {error}")

        finally:
            # ------------------------------------------------------------------
            # SECTION 19: CLOSE DATABASE CONNECTION
            # ------------------------------------------------------------------
            # Always release the metadata connection.
            if connection is not None:
                connection.close()

    def get_selected_column(self):
        # ------------------------------------------------------------------
        # SECTION 20: RETURN SELECTED COLUMN
        # ------------------------------------------------------------------
        selected_item = self.column_list.currentItem()

        if selected_item is None:
            return None

        # FULL_NAME (VARCHAR2) becomes FULL_NAME.
        return selected_item.text().split(" (", 1)[0]

    def get_selected_column_info(self):
        # ------------------------------------------------------------------
        # SECTION 21: RETURN SELECTED COLUMN METADATA
        # ------------------------------------------------------------------
        # Return both column name and Oracle metadata so datatype-aware
        # strategy selection can be performed.
        selected_item = self.column_list.currentItem()

        if selected_item is None:
            return None

        column_name = selected_item.text().split(" (", 1)[0]

        # Search the metadata previously returned by database_metadata.py.
        for column in self.table_columns:
            if column["column_name"] == column_name:
                return column.copy()

        return None

    def get_source_config(self):
        # ------------------------------------------------------------------
        # SECTION 22: RETURN SOURCE CONFIGURATION
        # ------------------------------------------------------------------
        # Other GUI components can request source settings without
        # directly accessing this panel's widgets.
        return {
            "source_schema": self.source_schema_input.text().strip().upper(),
            "source_table": self.source_table_input.text().strip().upper(),
            "table_columns": self.table_columns.copy()
        }

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 23: CLEAR SOURCE PANEL
        # ------------------------------------------------------------------
        # Remove the current source configuration and metadata.
        self.source_schema_input.clear()
        self.source_table_input.clear()
        self.column_list.clear()
        self.table_columns.clear()
        self.connection_config = None

        self.status_label.setStyleSheet("")
        self.status_label.setText("Status: Database connection not ready")