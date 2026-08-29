"""
Module: target_table_panel.py

Purpose:
Manages the OUT_PLACE target-table configuration in the GUI.

Main responsibilities:
- Accept the target Oracle schema and table name.
- Generate a default target table name from the selected source table.
- Receive the available source columns from SourceTablePanel.
- Allow selected source columns to be excluded from the target table.
- Prevent duplicate column exclusions.
- Allow exclusions to be removed.
- Return target-table configuration to preview and execution.
- Clear the target configuration when starting a new session.

This module does not create or drop Oracle tables, perform anonymization,
write data, or execute database transactions.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QListWidget,
    QAbstractItemView
)


class TargetTablePanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: STORE SOURCE AND EXCLUSION INFORMATION
        # ------------------------------------------------------------------
        # Source columns are supplied by SourceTablePanel after metadata
        # has been successfully loaded.
        self.source_columns = []

        # Columns listed here will not exist in the OUT_PLACE target table.
        self.excluded_columns = []

        # ------------------------------------------------------------------
        # SECTION 2: CREATE TARGET INPUT FIELDS
        # ------------------------------------------------------------------
        self.target_schema_input = QLineEdit()
        self.target_table_input = QLineEdit()

        self.target_schema_input.setPlaceholderText(
            "Target schema"
        )

        self.target_table_input.setPlaceholderText(
            "Target table"
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE COLUMN EXCLUSION CONTROLS
        # ------------------------------------------------------------------
        self.exclusion_combo = QComboBox()

        self.exclusion_combo.setEnabled(
            False
        )

        self.add_exclusion_button = QPushButton(
            "Add Exclusion"
        )

        self.add_exclusion_button.setEnabled(
            False
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE EXCLUDED-COLUMN LIST
        # ------------------------------------------------------------------
        self.excluded_columns_list = QListWidget()

        self.excluded_columns_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.excluded_columns_list.setMinimumHeight(
            100
        )

        self.remove_exclusion_button = QPushButton(
            "Remove Exclusion"
        )

        self.remove_exclusion_button.setEnabled(
            False
        )

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Load a source table to configure the target."
        )

        # ------------------------------------------------------------------
        # SECTION 6: CREATE TARGET TABLE LAYOUT
        # ------------------------------------------------------------------
        # Target schema and target table are displayed horizontally.
        target_grid = QGridLayout()

        target_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        target_grid.setHorizontalSpacing(
            10
        )

        target_grid.setVerticalSpacing(
            4
        )

        # --------------------------------------------------------------
        # LABEL ROW
        # --------------------------------------------------------------
        target_grid.addWidget(
            QLabel("Target Schema"),
            0,
            0
        )

        target_grid.addWidget(
            QLabel("Target Table"),
            0,
            1
        )

        # --------------------------------------------------------------
        # INPUT ROW
        # --------------------------------------------------------------
        target_grid.addWidget(
            self.target_schema_input,
            1,
            0
        )

        target_grid.addWidget(
            self.target_table_input,
            1,
            1
        )

        target_grid.setColumnStretch(
            0,
            1
        )

        target_grid.setColumnStretch(
            1,
            2
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE EXCLUSION SELECTION LAYOUT
        # ------------------------------------------------------------------
        exclusion_grid = QGridLayout()

        exclusion_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        exclusion_grid.setHorizontalSpacing(
            10
        )

        exclusion_grid.setVerticalSpacing(
            4
        )

        exclusion_grid.addWidget(
            QLabel("Column to Exclude"),
            0,
            0
        )

        exclusion_grid.addWidget(
            self.exclusion_combo,
            1,
            0
        )

        exclusion_grid.addWidget(
            self.add_exclusion_button,
            1,
            1
        )

        exclusion_grid.setColumnStretch(
            0,
            1
        )

        exclusion_grid.setColumnStretch(
            1,
            0
        )

        # ------------------------------------------------------------------
        # SECTION 8: CREATE EXCLUSION ACTION ROW
        # ------------------------------------------------------------------
        exclusion_action_layout = QHBoxLayout()

        exclusion_action_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        exclusion_action_layout.addStretch()

        exclusion_action_layout.addWidget(
            self.remove_exclusion_button
        )

        # ------------------------------------------------------------------
        # SECTION 9: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's numbered QGroupBox already supplies the outer margin.
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
            target_grid
        )

        layout.addSpacing(
            4
        )

        layout.addLayout(
            exclusion_grid
        )

        layout.addWidget(
            QLabel("Excluded Columns")
        )

        layout.addWidget(
            self.excluded_columns_list
        )

        layout.addLayout(
            exclusion_action_layout
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(
            layout
        )

        # ------------------------------------------------------------------
        # SECTION 10: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        self.add_exclusion_button.clicked.connect(
            self.add_exclusion
        )

        self.remove_exclusion_button.clicked.connect(
            self.remove_selected_exclusion
        )

        self.excluded_columns_list.itemSelectionChanged.connect(
            self.update_remove_button_state
        )

    def configure_from_source(
        self,
        source_table,
        column_names
    ):
        # ------------------------------------------------------------------
        # SECTION 11: RECEIVE SOURCE TABLE INFORMATION
        # ------------------------------------------------------------------
        # This method is called from MainWindow after source metadata
        # has been successfully loaded.
        source_table = (
            source_table or ""
        ).strip().upper()

        self.source_columns = [
            str(column).strip().upper()
            for column in column_names
            if column
        ]

        # ------------------------------------------------------------------
        # SECTION 12: CREATE DEFAULT TARGET TABLE NAME
        # ------------------------------------------------------------------
        # OUT_PLACE convention:
        #
        # DA_CUSTOMER
        #
        # becomes:
        #
        # DA_CUSTOMER_ANON
        if source_table:
            self.target_table_input.setText(
                f"{source_table}_ANON"
            )

        else:
            self.target_table_input.clear()

        # ------------------------------------------------------------------
        # SECTION 13: RESET PREVIOUS EXCLUSIONS
        # ------------------------------------------------------------------
        # Exclusions from another source table must never carry into a newly
        # loaded source table.
        self.excluded_columns.clear()
        self.excluded_columns_list.clear()

        # ------------------------------------------------------------------
        # SECTION 14: LOAD AVAILABLE EXCLUSION COLUMNS
        # ------------------------------------------------------------------
        self.refresh_exclusion_combo()

        if self.source_columns:
            self.exclusion_combo.setEnabled(
                True
            )

            self.add_exclusion_button.setEnabled(
                True
            )

            self.status_label.setStyleSheet("")

            self.status_label.setText(
                f"{len(self.source_columns)} source columns available. "
                f"Exclude columns only when they should not exist in the target."
            )

        else:
            self.exclusion_combo.setEnabled(
                False
            )

            self.add_exclusion_button.setEnabled(
                False
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "No source columns are available for target configuration."
            )

    def refresh_exclusion_combo(self):
        # ------------------------------------------------------------------
        # SECTION 15: REFRESH AVAILABLE EXCLUSION COLUMNS
        # ------------------------------------------------------------------
        # Only columns that have not already been excluded remain available
        # in the combo box.
        self.exclusion_combo.clear()

        available_columns = [
            column
            for column in self.source_columns
            if column not in self.excluded_columns
        ]

        self.exclusion_combo.addItems(
            available_columns
        )

        self.add_exclusion_button.setEnabled(
            bool(available_columns)
        )

    def add_exclusion(self):
        # ------------------------------------------------------------------
        # SECTION 16: VALIDATE AVAILABLE SOURCE METADATA
        # ------------------------------------------------------------------
        if not self.source_columns:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Load a source table before excluding columns."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 17: GET COLUMN TO EXCLUDE
        # ------------------------------------------------------------------
        column_name = (
            self.exclusion_combo
            .currentText()
            .strip()
            .upper()
        )

        if not column_name:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Select a source column to exclude."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 18: VALIDATE SOURCE COLUMN
        # ------------------------------------------------------------------
        if column_name not in self.source_columns:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Column {column_name} does not exist in the source table."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 19: PREVENT DUPLICATE EXCLUSIONS
        # ------------------------------------------------------------------
        if column_name in self.excluded_columns:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"{column_name} is already excluded."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 20: ADD COLUMN EXCLUSION
        # ------------------------------------------------------------------
        self.excluded_columns.append(
            column_name
        )

        self.refresh_excluded_columns()
        self.refresh_exclusion_combo()

        self.status_label.setStyleSheet(
            "color: green; font-weight: bold;"
        )

        self.status_label.setText(
            f"✓ {column_name} will be excluded from the target table."
        )

    def remove_selected_exclusion(self):
        # ------------------------------------------------------------------
        # SECTION 21: GET SELECTED EXCLUSION
        # ------------------------------------------------------------------
        selected_item = self.excluded_columns_list.currentItem()

        if selected_item is None:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Select an excluded column to remove."
            )

            return

        column_name = selected_item.text()

        # ------------------------------------------------------------------
        # SECTION 22: REMOVE COLUMN EXCLUSION
        # ------------------------------------------------------------------
        if column_name in self.excluded_columns:
            self.excluded_columns.remove(
                column_name
            )

        self.refresh_excluded_columns()
        self.refresh_exclusion_combo()

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"{column_name} restored to the target table."
        )

    def refresh_excluded_columns(self):
        # ------------------------------------------------------------------
        # SECTION 23: REFRESH EXCLUDED-COLUMN LIST
        # ------------------------------------------------------------------
        self.excluded_columns_list.clear()

        self.excluded_columns_list.addItems(
            self.excluded_columns
        )

        self.remove_exclusion_button.setEnabled(
            False
        )

    def update_remove_button_state(self):
        # ------------------------------------------------------------------
        # SECTION 24: UPDATE REMOVE BUTTON STATE
        # ------------------------------------------------------------------
        self.remove_exclusion_button.setEnabled(
            self.excluded_columns_list.currentItem() is not None
        )

    def get_target_config(self):
        # ------------------------------------------------------------------
        # SECTION 25: RETURN TARGET CONFIGURATION
        # ------------------------------------------------------------------
        # This structure is consumed by validation, preview, and execution.
        return {
            "target_schema": self.target_schema_input.text().strip().upper(),
            "target_table": self.target_table_input.text().strip().upper(),
            "excluded_columns": self.excluded_columns.copy()
        }

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 26: CLEAR TARGET CONFIGURATION
        # ------------------------------------------------------------------
        self.target_schema_input.clear()
        self.target_table_input.clear()

        self.source_columns.clear()
        self.excluded_columns.clear()

        self.exclusion_combo.clear()
        self.excluded_columns_list.clear()

        self.exclusion_combo.setEnabled(
            False
        )

        self.add_exclusion_button.setEnabled(
            False
        )

        self.remove_exclusion_button.setEnabled(
            False
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Load a source table to configure the target."
        )