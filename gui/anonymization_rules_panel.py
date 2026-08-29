"""
Module: anonymization_rules_panel.py

Purpose:
Manages column-level anonymization rules in the GUI.

Main responsibilities:
- Receive metadata for the currently selected source column.
- Display the selected source column and Oracle datatype.
- Show only anonymization strategies compatible with the datatype.
- Allow users to add or update anonymization rules.
- Display configured anonymization rules in a structured table.
- Allow users to remove selected anonymization rules.
- Return the current anonymization rules to preview and execution.
- Clear existing rules when the source table changes or the session resets.

This module does not retrieve Oracle metadata, perform anonymization,
create target tables, preview data, or execute anonymization.
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)

from validation.strategy_validator import (
    get_allowed_strategies,
    is_strategy_allowed
)


class AnonymizationRulesPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: INITIALIZE RULE STORAGE
        # ------------------------------------------------------------------
        # Core rule structure used by preview and execution:
        #
        # {
        #     "FULL_NAME": "TOKENIZATION",
        #     "DATE_OF_BIRTH": "DATE_SHIFT"
        # }
        self.rules = {}

        # Datatypes are stored separately for presentation purposes only.
        #
        # The actual anonymization configuration returned by get_rules()
        # remains the simple column -> strategy dictionary.
        self.rule_datatypes = {}

        # ------------------------------------------------------------------
        # SECTION 2: CREATE SELECTED COLUMN DISPLAY
        # ------------------------------------------------------------------
        # These fields are informational. The actual selected column comes
        # from SourceTablePanel.
        self.selected_column_input = QLineEdit()
        self.selected_column_input.setReadOnly(True)
        self.selected_column_input.setPlaceholderText(
            "Select a column in Source Data"
        )

        self.data_type_input = QLineEdit()
        self.data_type_input.setReadOnly(True)
        self.data_type_input.setPlaceholderText(
            "Oracle datatype"
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE STRATEGY COMBO
        # ------------------------------------------------------------------
        self.strategy_combo = QComboBox()

        # No strategy can be selected until a source column has been selected.
        self.strategy_combo.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 4: CREATE RULE ACTION BUTTONS
        # ------------------------------------------------------------------
        self.add_rule_button = QPushButton(
            "Add Rule"
        )

        # MainWindow owns the Add Rule connection because it needs to obtain
        # the currently selected source-column metadata first.
        self.add_rule_button.setObjectName(
            "primaryButton"
        )

        self.add_rule_button.setEnabled(False)

        self.remove_rule_button = QPushButton(
            "Remove Rule"
        )

        self.remove_rule_button.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 5: CREATE RULES TABLE
        # ------------------------------------------------------------------
        self.rules_list = QTableWidget()

        self.rules_list.setColumnCount(3)

        self.rules_list.setHorizontalHeaderLabels([
            "Column Name",
            "Data Type",
            "Strategy"
        ])

        self.rules_list.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.rules_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.rules_list.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.rules_list.setAlternatingRowColors(
            True
        )

        self.rules_list.verticalHeader().setVisible(
            False
        )

        header = self.rules_list.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch
        )

        self.rules_list.setMinimumHeight(
            150
        )

        # ------------------------------------------------------------------
        # SECTION 6: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Select a source column to configure an anonymization rule."
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE RULE CONFIGURATION ROW
        # ------------------------------------------------------------------
        rule_grid = QGridLayout()

        rule_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        rule_grid.setHorizontalSpacing(
            10
        )

        rule_grid.setVerticalSpacing(
            4
        )

        # --------------------------------------------------------------
        # LABEL ROW
        # --------------------------------------------------------------
        rule_grid.addWidget(
            QLabel("Selected Column"),
            0,
            0
        )

        rule_grid.addWidget(
            QLabel("Data Type"),
            0,
            1
        )

        rule_grid.addWidget(
            QLabel("Strategy"),
            0,
            2
        )

        # --------------------------------------------------------------
        # CONTROL ROW
        # --------------------------------------------------------------
        rule_grid.addWidget(
            self.selected_column_input,
            1,
            0
        )

        rule_grid.addWidget(
            self.data_type_input,
            1,
            1
        )

        rule_grid.addWidget(
            self.strategy_combo,
            1,
            2
        )

        rule_grid.addWidget(
            self.add_rule_button,
            1,
            3
        )

        rule_grid.setColumnStretch(
            0,
            2
        )

        rule_grid.setColumnStretch(
            1,
            1
        )

        rule_grid.setColumnStretch(
            2,
            2
        )

        rule_grid.setColumnStretch(
            3,
            0
        )

        # ------------------------------------------------------------------
        # SECTION 8: CREATE RULE TABLE ACTION ROW
        # ------------------------------------------------------------------
        rule_action_layout = QHBoxLayout()

        rule_action_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        rule_action_layout.addStretch()

        rule_action_layout.addWidget(
            self.remove_rule_button
        )

        # ------------------------------------------------------------------
        # SECTION 9: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's numbered QGroupBox already provides outer spacing.
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            5
        )

        layout.addLayout(
            rule_grid
        )

        layout.addWidget(
            QLabel("Configured Rules")
        )

        layout.addWidget(
            self.rules_list
        )

        layout.addLayout(
            rule_action_layout
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(
            layout
        )

        # ------------------------------------------------------------------
        # SECTION 10: CONNECT INTERNAL GUI EVENTS
        # ------------------------------------------------------------------
        # Add Rule remains connected from MainWindow.
        #
        # Remove Rule can be handled completely inside this panel.
        self.remove_rule_button.clicked.connect(
            self.remove_selected_rule
        )

        self.rules_list.itemSelectionChanged.connect(
            self.update_remove_button_state
        )

    def configure_strategies(
        self,
        column_info
    ):
        # ------------------------------------------------------------------
        # SECTION 11: RESET STRATEGY SELECTION
        # ------------------------------------------------------------------
        self.strategy_combo.clear()

        # ------------------------------------------------------------------
        # SECTION 12: HANDLE NO SOURCE COLUMN SELECTED
        # ------------------------------------------------------------------
        if not column_info:
            self.selected_column_input.clear()
            self.data_type_input.clear()

            self.strategy_combo.setEnabled(
                False
            )

            self.add_rule_button.setEnabled(
                False
            )

            self.status_label.setStyleSheet("")

            self.status_label.setText(
                "Select a source column to configure an anonymization rule."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 13: READ COLUMN METADATA
        # ------------------------------------------------------------------
        column_name = column_info.get(
            "column_name"
        )

        data_type = column_info.get(
            "data_type"
        )

        if column_name:
            column_name = str(
                column_name
            ).upper()

        if data_type:
            data_type = str(
                data_type
            ).upper()

        self.selected_column_input.setText(
            column_name or ""
        )

        self.data_type_input.setText(
            data_type or ""
        )

        # ------------------------------------------------------------------
        # SECTION 14: DETERMINE COMPATIBLE STRATEGIES
        # ------------------------------------------------------------------
        allowed_strategies = get_allowed_strategies(
            data_type
        )

        # ------------------------------------------------------------------
        # SECTION 15: HANDLE UNSUPPORTED DATATYPE
        # ------------------------------------------------------------------
        if not allowed_strategies:
            self.strategy_combo.setEnabled(
                False
            )

            self.add_rule_button.setEnabled(
                False
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"No anonymization strategy is available for datatype "
                f"{data_type}."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 16: LOAD COMPATIBLE STRATEGIES
        # ------------------------------------------------------------------
        self.strategy_combo.addItems(
            allowed_strategies
        )

        self.strategy_combo.setEnabled(
            True
        )

        self.add_rule_button.setEnabled(
            True
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"{len(allowed_strategies)} compatible strategy option(s) "
            f"available for {column_name}."
        )

        # ------------------------------------------------------------------
        # SECTION 17: RESTORE EXISTING RULE SELECTION
        # ------------------------------------------------------------------
        # If the selected column already has a rule, display the existing
        # strategy automatically. This makes rule updates easier.
        existing_strategy = self.rules.get(
            column_name
        )

        if existing_strategy:
            strategy_index = self.strategy_combo.findText(
                existing_strategy
            )

            if strategy_index >= 0:
                self.strategy_combo.setCurrentIndex(
                    strategy_index
                )

    def add_rule(
        self,
        column_info
    ):
        # ------------------------------------------------------------------
        # SECTION 18: VALIDATE SELECTED SOURCE COLUMN
        # ------------------------------------------------------------------
        if not column_info:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Select a source column first."
            )

            return

        column_name = column_info.get(
            "column_name"
        )

        data_type = column_info.get(
            "data_type"
        )

        if not column_name or not data_type:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "The selected source column metadata is incomplete."
            )

            return

        column_name = str(
            column_name
        ).upper()

        data_type = str(
            data_type
        ).upper()

        # ------------------------------------------------------------------
        # SECTION 19: VALIDATE SELECTED STRATEGY
        # ------------------------------------------------------------------
        strategy = self.strategy_combo.currentText().strip().upper()

        if not strategy:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Select an anonymization strategy."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 20: REVALIDATE DATATYPE COMPATIBILITY
        # ------------------------------------------------------------------
        # The combo box is already filtered by datatype, but compatibility
        # is checked again before the rule enters the execution configuration.
        if not is_strategy_allowed(
            data_type,
            strategy
        ):
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"{strategy} is not compatible with datatype {data_type}."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 21: ADD OR UPDATE RULE
        # ------------------------------------------------------------------
        existing_rule = column_name in self.rules

        self.rules[column_name] = strategy
        self.rule_datatypes[column_name] = data_type

        self.refresh_rules()

        self.status_label.setStyleSheet(
            "color: green; font-weight: bold;"
        )

        if existing_rule:
            self.status_label.setText(
                f"✓ Rule updated: {column_name} → {strategy}"
            )

        else:
            self.status_label.setText(
                f"✓ Rule added: {column_name} → {strategy}"
            )

    def remove_selected_rule(self):
        # ------------------------------------------------------------------
        # SECTION 22: GET SELECTED RULE
        # ------------------------------------------------------------------
        selected_row = self.rules_list.currentRow()

        if selected_row < 0:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Select a configured rule to remove."
            )

            return

        column_item = self.rules_list.item(
            selected_row,
            0
        )

        if column_item is None:
            return

        column_name = column_item.text()

        # ------------------------------------------------------------------
        # SECTION 23: REMOVE RULE
        # ------------------------------------------------------------------
        self.rules.pop(
            column_name,
            None
        )

        self.rule_datatypes.pop(
            column_name,
            None
        )

        self.refresh_rules()

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            f"Rule removed for {column_name}."
        )

    def refresh_rules(self):
        # ------------------------------------------------------------------
        # SECTION 24: REFRESH RULES TABLE
        # ------------------------------------------------------------------
        self.rules_list.setRowCount(
            len(self.rules)
        )

        for row, (column_name, strategy) in enumerate(
            self.rules.items()
        ):
            data_type = self.rule_datatypes.get(
                column_name,
                ""
            )

            self.rules_list.setItem(
                row,
                0,
                QTableWidgetItem(column_name)
            )

            self.rules_list.setItem(
                row,
                1,
                QTableWidgetItem(data_type)
            )

            self.rules_list.setItem(
                row,
                2,
                QTableWidgetItem(strategy)
            )

        # There is no selected rule after rebuilding the table.
        self.remove_rule_button.setEnabled(
            False
        )

    def update_remove_button_state(self):
        # ------------------------------------------------------------------
        # SECTION 25: ENABLE REMOVE ONLY WHEN A RULE IS SELECTED
        # ------------------------------------------------------------------
        selected_row = self.rules_list.currentRow()

        self.remove_rule_button.setEnabled(
            selected_row >= 0
        )

    def clear_rules(self):
        # ------------------------------------------------------------------
        # SECTION 26: CLEAR ANONYMIZATION RULES
        # ------------------------------------------------------------------
        self.rules.clear()
        self.rule_datatypes.clear()

        self.rules_list.setRowCount(
            0
        )

        self.selected_column_input.clear()
        self.data_type_input.clear()

        self.strategy_combo.clear()

        self.strategy_combo.setEnabled(
            False
        )

        self.add_rule_button.setEnabled(
            False
        )

        self.remove_rule_button.setEnabled(
            False
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Select a source column to configure an anonymization rule."
        )

    def get_rules(self):
        # ------------------------------------------------------------------
        # SECTION 27: RETURN CURRENT RULE CONFIGURATION
        # ------------------------------------------------------------------
        # Return a copy so external components cannot accidentally modify
        # the panel's internal rule dictionary.
        return self.rules.copy()