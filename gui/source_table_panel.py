"""
Module: source_table_panel.py

Purpose:
Handles source Oracle table selection and source table metadata in the GUI.

Main responsibilities:
- Accept source schema and table names from the user.
- Receive a successfully tested GUI database connection configuration.
- Use the GUI connection configuration when retrieving source metadata.
- Retrieve source table metadata using database_metadata.py.
- Display available source columns and Oracle datatypes.
- Allow a source column to be selected for anonymization-rule configuration.
- Return the currently selected source column.
- Return metadata for the currently selected source column.
- Return the current source-table configuration.
- Notify other GUI components when source columns are successfully loaded.
- Clear the current source configuration when starting a new session.
- Record source metadata loading activity in the technical log.

This module does not test database connections, perform anonymization,
create target tables, or modify Oracle source data.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)

from database.oracle_connection import connect_to_oracle
from database.database_metadata import get_table_columns
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
logger = get_logger()


class SourceTablePanel(QWidget):

    # ------------------------------------------------------------------
    # SIGNAL: SOURCE COLUMNS LOADED
    # ------------------------------------------------------------------
    # Sends:
    #
    # 1. Source table name
    # 2. List of source column names
    #
    # MainWindow uses this signal to configure other GUI components.
    columns_loaded = Signal(str, object)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CREATE SOURCE INPUT FIELDS
        # ------------------------------------------------------------------
        self.source_schema_input = QLineEdit()
        self.source_table_input = QLineEdit()

        self.source_schema_input.setPlaceholderText("Source schema")
        self.source_table_input.setPlaceholderText("Source table")

        # ------------------------------------------------------------------
        # SECTION 3: CREATE LOAD COLUMNS BUTTON
        # ------------------------------------------------------------------
        self.load_columns_button = QPushButton("Load Columns")
        self.load_columns_button.setObjectName("primaryButton")

        # ------------------------------------------------------------------
        # SECTION 4: CREATE SOURCE COLUMN TABLE
        # ------------------------------------------------------------------
        # Keep the attribute name column_list because MainWindow already
        # connects to column_list.itemSelectionChanged.
        #
        # Internally it is now a QTableWidget rather than QListWidget.
        self.column_list = QTableWidget()

        self.column_list.setColumnCount(2)
        self.column_list.setHorizontalHeaderLabels([
            "Column Name",
            "Data Type"
        ])

        # Select a complete metadata row instead of one individual cell.
        self.column_list.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.column_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Metadata is informational and must not be edited by the user.
        self.column_list.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Alternate row shading improves readability when tables contain
        # many Oracle columns.
        self.column_list.setAlternatingRowColors(True)

        # Row numbers do not add useful information here.
        self.column_list.verticalHeader().setVisible(False)

        # Allow the column name to use most of the available space.
        header = self.column_list.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # Keep Section 2 compact while still displaying several columns.
        self.column_list.setMinimumHeight(160)

        # ------------------------------------------------------------------
        # SECTION 5: STORE SOURCE METADATA
        # ------------------------------------------------------------------
        # Full Oracle metadata is retained because later GUI components
        # require both the column name and datatype.
        self.table_columns = []

        # Successfully tested GUI database configuration supplied through
        # MainWindow from DatabaseConnectionPanel.
        self.connection_config = None

        # ------------------------------------------------------------------
        # SECTION 6: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Database connection not ready."
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE COMPACT SOURCE SELECTION LAYOUT
        # ------------------------------------------------------------------
        source_grid = QGridLayout()

        source_grid.setContentsMargins(0, 0, 0, 0)
        source_grid.setHorizontalSpacing(10)
        source_grid.setVerticalSpacing(4)

        # --------------------------------------------------------------
        # LABEL ROW
        # --------------------------------------------------------------
        source_grid.addWidget(
            QLabel("Source Schema"),
            0,
            0
        )

        source_grid.addWidget(
            QLabel("Source Table"),
            0,
            1
        )

        # --------------------------------------------------------------
        # INPUT ROW
        # --------------------------------------------------------------
        source_grid.addWidget(
            self.source_schema_input,
            1,
            0
        )

        source_grid.addWidget(
            self.source_table_input,
            1,
            1
        )

        source_grid.addWidget(
            self.load_columns_button,
            1,
            2
        )

        # Source table normally needs slightly more horizontal space
        # than the schema name.
        source_grid.setColumnStretch(0, 1)
        source_grid.setColumnStretch(1, 2)
        source_grid.setColumnStretch(2, 0)

        # ------------------------------------------------------------------
        # SECTION 8: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's numbered QGroupBox already provides outer spacing.
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        layout.addLayout(source_grid)

        layout.addWidget(
            QLabel("Available Columns")
        )

        layout.addWidget(
            self.column_list
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 9: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        self.load_columns_button.clicked.connect(
            self.load_columns
        )

    def set_connection_config(self, connection_config):
        # ------------------------------------------------------------------
        # SECTION 10: RECEIVE DATABASE CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # MainWindow passes the successfully tested in-memory configuration
        # received from DatabaseConnectionPanel.
        self.connection_config = connection_config

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Database connection ready. Select a source table."
        )

    def load_columns(self):
        # ------------------------------------------------------------------
        # SECTION 11: READ SOURCE SCHEMA AND TABLE
        # ------------------------------------------------------------------
        source_schema = self.source_schema_input.text().strip().upper()
        source_table = self.source_table_input.text().strip().upper()

        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE SOURCE SCHEMA
        # ------------------------------------------------------------------
        if not source_schema:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Enter the source schema."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 13: VALIDATE SOURCE TABLE
        # ------------------------------------------------------------------
        if not source_table:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Enter the source table."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 14: VALIDATE DATABASE CONNECTION
        # ------------------------------------------------------------------
        if self.connection_config is None:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Test the database connection first."
            )

            logger.warning(
                "Source metadata request stopped because no tested GUI "
                "database connection was available."
            )

            return

        connection = None

        try:
            # ------------------------------------------------------------------
            # SECTION 15: PREPARE METADATA LOADING
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")

            self.status_label.setText(
                "Loading source columns..."
            )

            self.column_list.setRowCount(0)
            self.table_columns = []

            # ------------------------------------------------------------------
            # SECTION 16: CONNECT TO ORACLE
            # ------------------------------------------------------------------
            connection = connect_to_oracle(
                self.connection_config
            )

            # ------------------------------------------------------------------
            # SECTION 17: RETRIEVE SOURCE TABLE METADATA
            # ------------------------------------------------------------------
            self.table_columns = get_table_columns(
                connection,
                source_schema,
                source_table
            )

            # ------------------------------------------------------------------
            # SECTION 18: HANDLE TABLE NOT FOUND / NO COLUMNS
            # ------------------------------------------------------------------
            if not self.table_columns:
                self.status_label.setStyleSheet(
                    "color: red; font-weight: bold;"
                )

                self.status_label.setText(
                    f"Table {source_schema}.{source_table} "
                    f"was not found or no columns were available."
                )

                logger.warning(
                    "Source metadata returned no columns | Source=%s.%s",
                    source_schema,
                    source_table
                )

                return

            # ------------------------------------------------------------------
            # SECTION 19: DISPLAY SOURCE COLUMN METADATA
            # ------------------------------------------------------------------
            self.column_list.setRowCount(
                len(self.table_columns)
            )

            for row, column in enumerate(self.table_columns):
                column_name = column["column_name"]
                data_type = column["data_type"]

                column_item = QTableWidgetItem(
                    column_name
                )

                datatype_item = QTableWidgetItem(
                    data_type
                )

                self.column_list.setItem(
                    row,
                    0,
                    column_item
                )

                self.column_list.setItem(
                    row,
                    1,
                    datatype_item
                )

            # ------------------------------------------------------------------
            # SECTION 20: REPORT SUCCESS
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet(
                "color: green; font-weight: bold;"
            )

            self.status_label.setText(
                f"✓ {len(self.table_columns)} columns loaded from "
                f"{source_schema}.{source_table}."
            )

            logger.info(
                "Source metadata loaded successfully | "
                "Source=%s.%s | Columns=%s",
                source_schema,
                source_table,
                len(self.table_columns)
            )

            # ------------------------------------------------------------------
            # SECTION 21: NOTIFY OTHER GUI COMPONENTS
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
            # SECTION 22: HANDLE METADATA FAILURE
            # ------------------------------------------------------------------
            self.column_list.setRowCount(0)
            self.table_columns = []

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Unable to load source columns: {error}"
            )

            logger.exception(
                "Source metadata loading failed | "
                "Source=%s.%s | Error=%s",
                source_schema,
                source_table,
                error
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 23: CLOSE DATABASE CONNECTION
            # ------------------------------------------------------------------
            if connection is not None:
                connection.close()

    def get_selected_column(self):
        # ------------------------------------------------------------------
        # SECTION 24: RETURN SELECTED COLUMN NAME
        # ------------------------------------------------------------------
        selected_row = self.column_list.currentRow()

        if selected_row < 0:
            return None

        column_item = self.column_list.item(
            selected_row,
            0
        )

        if column_item is None:
            return None

        return column_item.text()

    def get_selected_column_info(self):
        # ------------------------------------------------------------------
        # SECTION 25: RETURN SELECTED COLUMN METADATA
        # ------------------------------------------------------------------
        # AnonymizationRulesPanel requires the Oracle datatype in addition
        # to the column name so it can filter compatible strategies.
        column_name = self.get_selected_column()

        if column_name is None:
            return None

        for column in self.table_columns:
            if column["column_name"] == column_name:
                return column.copy()

        return None

    def get_source_config(self):
        # ------------------------------------------------------------------
        # SECTION 26: RETURN SOURCE CONFIGURATION
        # ------------------------------------------------------------------
        return {
            "source_schema": self.source_schema_input.text().strip().upper(),
            "source_table": self.source_table_input.text().strip().upper(),
            "table_columns": self.table_columns.copy()
        }

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 27: CLEAR SOURCE PANEL
        # ------------------------------------------------------------------
        self.source_schema_input.clear()
        self.source_table_input.clear()

        self.column_list.setRowCount(0)
        self.table_columns.clear()

        # Start Afresh also clears DatabaseConnectionPanel, therefore
        # discard the previously supplied connection configuration.
        self.connection_config = None

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Database connection not ready."
        )