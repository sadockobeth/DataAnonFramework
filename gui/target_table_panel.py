"""
Module: target_table_panel.py

Purpose:
Manages OUT_PLACE target-table configuration in the GUI.

Main responsibilities:
- Accept the target Oracle schema and target table name.
- Automatically suggest a target table name based on the source table.
- Receive available source columns from source_table_panel.py.
- Allow the user to exclude columns from the target table.
- Remove exclusions that were selected incorrectly.
- Return the target configuration to other parts of the application.
- Clear the current target configuration and exclusions.

This module does not create the Oracle target table or write data.
"""

from PySide6.QtWidgets import(
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget,
    QComboBox
)

class TargetTablePanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: INITIALIZE EXCLUDED COLUMNS
        # ------------------------------------------------------------------
        # This list stores columns that should not exist in the OUT_PLACE target table.
        self.excluded_columns = []

        # ------------------------------------------------------------------
        # SECTION 2: CREATE TARGET INPUT FIELDS
        # ------------------------------------------------------------------
        # QLineEdit allows the user to enter the target Oracle schema
        # and target table name.
        self.target_schema_input = QLineEdit()
        self.target_table_input = QLineEdit()

        # ------------------------------------------------------------------
        # SECTION 3: CREATE COLUMN EXCLUSION DROP-DOWN
        # ------------------------------------------------------------------
        # QComboBox will contain the columns loaded from the source table.
        # The user can select a column that should be excluded from the target.
        self.exclude_column_combo = QComboBox()

        # ------------------------------------------------------------------
        # SECTION 4: CREATE EXCLUSION BUTTONS
        # ------------------------------------------------------------------
        # Add Exclusion removes a column from the future target structure.
        # Remove Exclusion allows an incorrectly selected exclusion to be undone.
        self.add_exclusion_button = QPushButton("Add Exclusion")
        self.remove_exclusion_button = QPushButton("Remove Exclusion")

        # ------------------------------------------------------------------
        # SECTION 5: CREATE EXCLUDED COLUMNS LIST
        # ------------------------------------------------------------------
        # QListWidget displays all columns currently selected for exclusion.
        self.excluded_columns_list = QListWidget()

        # ------------------------------------------------------------------
        # SECTION 6: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # QLabel displays information about exclusions and target configuration.
        self.status_label = QLabel("No columns excluded.")

        # ------------------------------------------------------------------
        # SECTION 7: CREATE TARGET FORM LAYOUT
        # ------------------------------------------------------------------
        # QFormLayout places labels beside the target input fields.
        form_layout = QFormLayout()
        form_layout.addRow("Target Schema:", self.target_schema_input)
        form_layout.addRow("Target Table:", self.target_table_input)

        # ------------------------------------------------------------------
        # SECTION 8: CREATE EXCLUSION ACTION LAYOUT
        # ------------------------------------------------------------------
        # QHBoxLayout keeps the column selector and action buttons on the same horizontal row.
        exclusion_layout = QHBoxLayout()
        exclusion_layout.addWidget(QLabel("Exclude Column:"))
        exclusion_layout.addWidget(self.exclude_column_combo)
        exclusion_layout.addWidget(self.add_exclusion_button)
        exclusion_layout.addWidget(self.remove_exclusion_button)

        # ------------------------------------------------------------------
        # SECTION 9: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout arranges target configuration controls vertically.
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(exclusion_layout)
        layout.addWidget(QLabel("Excluded Target Columns:"))
        layout.addWidget(self.excluded_columns_list)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 10: CONNECT BUTTONS TO FUNCTIONS
        # ------------------------------------------------------------------
        # Each button is connected to the method responsible for changing
        # the exclusion list.
        self.add_exclusion_button.clicked.connect(self.add_exclusion)
        self.remove_exclusion_button.clicked.connect(self.remove_selected_exclusion)

    def configure_from_source(self, source_table, column_names):
        # ------------------------------------------------------------------
        # SECTION 11: RECEIVE SOURCE TABLE INFORMATION
        # ------------------------------------------------------------------
        # This method is called automatically after source columns are loaded.
        # A default target name such as DA_CUSTOMER_ANON is suggested.
        self.target_table_input.setText(f"{source_table}_ANON")

        # ------------------------------------------------------------------
        # SECTION 12: LOAD AVAILABLE EXCLUSION COLUMNS
        # ------------------------------------------------------------------
        # Replace columns from any previously loaded source table.
        self.exclude_column_combo.clear()
        self.exclude_column_combo.addItems(column_names)

        # Loading another source table also clears old exclusions because
        # they may not belong to the newly selected table.
        self.excluded_columns.clear()
        self.excluded_columns_list.clear()
        self.status_label.setText("No columns excluded.")

    def add_exclusion(self):
        # ------------------------------------------------------------------
        # SECTION 13: ADD COLUMN EXCLUSION
        # ------------------------------------------------------------------
        # currentText() returns the column selected in the QComboBox.
        column_name = self.exclude_column_combo.currentText()

        if not column_name:
            self.status_label.setText("No source column available.")
            return

        # Do not add the same column more than once.
        if column_name in self.excluded_columns:
            self.status_label.setText(f"{column_name} is already excluded.")
            return

        self.excluded_columns.append(column_name)
        self.refresh_exclusions()
        self.status_label.setText(f"Excluded: {column_name}")

    def remove_selected_exclusion(self):
        # ------------------------------------------------------------------
        # SECTION 14: REMOVE SELECTED EXCLUSION
        # ------------------------------------------------------------------
        # The user selects an existing exclusion from QListWidget
        # and clicks Remove Exclusion.
        selected_item = self.excluded_columns_list.currentItem()

        if selected_item is None:
            self.status_label.setText("Select an excluded column to remove.")
            return

        column_name = selected_item.text()
        self.excluded_columns.remove(column_name)

        self.refresh_exclusions()
        self.status_label.setText(f"Removed exclusion: {column_name}")

    def refresh_exclusions(self):
        # ------------------------------------------------------------------
        # SECTION 15: REFRESH EXCLUSION DISPLAY
        # ------------------------------------------------------------------
        # Rebuild QListWidget so it always matches excluded_columns.
        self.excluded_columns_list.clear()

        for column_name in self.excluded_columns:
            self.excluded_columns_list.addItem(column_name)

    def get_target_config(self):
        # ------------------------------------------------------------------
        # SECTION 16: RETURN TARGET CONFIGURATION
        # ------------------------------------------------------------------
        # Later the execution stage can request all target settings
        # through this single method.
        return {
            "target_schema": self.target_schema_input.text().strip().upper(),
            "target_table": self.target_table_input.text().strip().upper(),
            "excluded_columns": self.excluded_columns.copy()
        }

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 17: CLEAR TARGET PANEL
        # ------------------------------------------------------------------
        # Remove target configuration, available exclusion columns,
        # and all previously selected exclusions.
        self.target_schema_input.clear()
        self.target_table_input.clear()
        self.exclude_column_combo.clear()
        self.excluded_columns.clear()
        self.excluded_columns_list.clear()
        self.status_label.setText("No columns excluded.")