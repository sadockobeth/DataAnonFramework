"""
Module: anonymization_rules_panel.py

Purpose:
Manages datatype-aware anonymization rules selected by the user in the GUI.

Main responsibilities:
- Receive metadata for the currently selected source column.
- Display only anonymization strategies compatible with its Oracle datatype.
- Associate a selected source column with an anonymization strategy.
- Store column-to-strategy rules in a dictionary.
- Display the selected anonymization rules.
- Remove rules that were selected incorrectly.
- Clear rules when another source table or session is started.
- Return the current rules to other parts of the application.

This module does not perform the actual anonymization.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QComboBox

from validation.strategy_validator import get_allowed_strategies, is_strategy_allowed


class AnonymizationRulesPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: INITIALIZE ANONYMIZATION RULES
        # ------------------------------------------------------------------
        # The dictionary stores each selected column and its strategy.
        #
        # Example:
        # {
        #     "FULL_NAME": "TOKENIZATION",
        #     "NATIONAL_ID": "MASKING"
        # }
        self.rules = {}

        # ------------------------------------------------------------------
        # SECTION 2: CREATE STRATEGY DROP-DOWN
        # ------------------------------------------------------------------
        # QComboBox will display only strategies compatible with the
        # datatype of the currently selected Oracle column.
        self.strategy_combo = QComboBox()
        self.strategy_combo.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 3: CREATE RULE ACTION BUTTONS
        # ------------------------------------------------------------------
        # Add Rule assigns the selected strategy to the selected column.
        # Remove Rule removes an incorrectly selected rule.
        self.add_rule_button = QPushButton("Add Rule")
        self.remove_rule_button = QPushButton("Remove Rule")

        # Add Rule remains disabled until a supported column is selected.
        self.add_rule_button.setEnabled(False)

        # ------------------------------------------------------------------
        # SECTION 4: CREATE RULES LIST
        # ------------------------------------------------------------------
        # QListWidget displays rules currently selected by the user.
        self.rules_list = QListWidget()

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # QLabel reports column selection, rule additions, removals, and errors.
        self.status_label = QLabel("Select a source column.")

        # ------------------------------------------------------------------
        # SECTION 6: CREATE STRATEGY LAYOUT
        # ------------------------------------------------------------------
        # QHBoxLayout places the strategy selector and buttons on one row.
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Strategy:"))
        strategy_layout.addWidget(self.strategy_combo)
        strategy_layout.addWidget(self.add_rule_button)
        strategy_layout.addWidget(self.remove_rule_button)

        # ------------------------------------------------------------------
        # SECTION 7: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()
        layout.addLayout(strategy_layout)
        layout.addWidget(QLabel("Selected Anonymization Rules:"))
        layout.addWidget(self.rules_list)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 8: CONNECT REMOVE BUTTON
        # ------------------------------------------------------------------
        # Rule removal is completely managed by this panel.
        self.remove_rule_button.clicked.connect(self.remove_selected_rule)

    def configure_strategies(self, column_info):
        # ------------------------------------------------------------------
        # SECTION 9: CONFIGURE STRATEGIES FOR SELECTED COLUMN
        # ------------------------------------------------------------------
        # Clear strategies belonging to the previously selected column.
        self.strategy_combo.clear()

        if column_info is None:
            self.strategy_combo.setEnabled(False)
            self.add_rule_button.setEnabled(False)
            self.status_label.setText("Select a source column.")
            return

        column_name = column_info["column_name"]
        data_type = column_info["data_type"]

        # Ask the shared strategy validator which methods are compatible
        # with the selected Oracle datatype.
        allowed_strategies = get_allowed_strategies(data_type)

        # ------------------------------------------------------------------
        # SECTION 10: HANDLE UNSUPPORTED DATATYPE
        # ------------------------------------------------------------------
        # If no strategy supports this datatype, prevent rule creation.
        if not allowed_strategies:
            self.strategy_combo.setEnabled(False)
            self.add_rule_button.setEnabled(False)
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText(f"No supported strategy for {column_name} ({data_type}).")
            return

        # ------------------------------------------------------------------
        # SECTION 11: DISPLAY COMPATIBLE STRATEGIES
        # ------------------------------------------------------------------
        # Populate the drop-down only with valid strategies.
        self.strategy_combo.addItems(allowed_strategies)
        self.strategy_combo.setEnabled(True)
        self.add_rule_button.setEnabled(True)

        self.status_label.setStyleSheet("")
        self.status_label.setText(f"Selected: {column_name} ({data_type})")

    def add_rule(self, column_info):
        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE SELECTED COLUMN
        # ------------------------------------------------------------------
        if column_info is None:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText("Select a source column first.")
            return

        column_name = column_info["column_name"]
        data_type = column_info["data_type"]
        strategy = self.strategy_combo.currentText()

        # ------------------------------------------------------------------
        # SECTION 13: VALIDATE STRATEGY AGAIN
        # ------------------------------------------------------------------
        # Even though the drop-down already filters strategies, validate
        # again before storing the rule for additional protection.
        if not strategy or not is_strategy_allowed(data_type, strategy):
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText(f"{strategy} is not valid for {column_name} ({data_type}).")
            return

        # ------------------------------------------------------------------
        # SECTION 14: STORE ANONYMIZATION RULE
        # ------------------------------------------------------------------
        # Existing rules for the same column are automatically replaced.
        self.rules[column_name] = strategy

        self.refresh_rules()

        self.status_label.setStyleSheet("")
        self.status_label.setText(f"Added: {column_name} -> {strategy}")

    def remove_selected_rule(self):
        # ------------------------------------------------------------------
        # SECTION 15: REMOVE SELECTED RULE
        # ------------------------------------------------------------------
        # The user selects a rule from rules_list and clicks Remove Rule.
        selected_item = self.rules_list.currentItem()

        if selected_item is None:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_label.setText("Select a rule to remove.")
            return

        column_name = selected_item.text().split(" -> ", 1)[0]

        self.rules.pop(column_name, None)
        self.refresh_rules()

        self.status_label.setStyleSheet("")
        self.status_label.setText(f"Removed rule for {column_name}.")

    def refresh_rules(self):
        # ------------------------------------------------------------------
        # SECTION 16: REFRESH RULES DISPLAY
        # ------------------------------------------------------------------
        # Rebuild QListWidget from the current rules dictionary.
        self.rules_list.clear()

        for column_name, strategy in self.rules.items():
            self.rules_list.addItem(f"{column_name} -> {strategy}")

    def clear_rules(self):
        # ------------------------------------------------------------------
        # SECTION 17: CLEAR ALL RULES
        # ------------------------------------------------------------------
        # Remove rules and reset datatype-aware strategy selection.
        self.rules.clear()
        self.rules_list.clear()
        self.strategy_combo.clear()
        self.strategy_combo.setEnabled(False)
        self.add_rule_button.setEnabled(False)

        self.status_label.setStyleSheet("")
        self.status_label.setText("Select a source column.")

    def get_rules(self):
        # ------------------------------------------------------------------
        # SECTION 18: RETURN CURRENT RULES
        # ------------------------------------------------------------------
        # Return a copy so other components do not directly modify
        # this panel's internal rules dictionary.
        return self.rules.copy()