"""
Module: main_window.py

Purpose:
Assembles and coordinates the main DataAnonFramework GUI window.

Main responsibilities:
- Create and display the major GUI panels.
- Pass successfully tested database configuration between GUI components.
- Coordinate source metadata, datatype-aware strategies, preview, and execution.
- Receive and display anonymization execution summaries.
- Save completed execution summaries into persistent execution history.
- Refresh the execution-history panel after each execution.
- Protect configuration controls while anonymization is running.
- Prevent Clear / Start Afresh during active execution.
- Prevent application closure while the background QThread is active.
- Provide a scrollable main application area.
- Coordinate communication between GUI components.

This module should remain lightweight and should not contain database
access, anonymization algorithms, target-table creation, or data-writing logic.
"""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QMessageBox
)

from gui.database_connection_panel import DatabaseConnectionPanel
from gui.source_table_panel import SourceTablePanel
from gui.anonymization_rules_panel import AnonymizationRulesPanel
from gui.target_table_panel import TargetTablePanel
from gui.validation_preview_panel import ValidationPreviewPanel
from gui.execution_panel import ExecutionPanel
from gui.execution_summary_panel import ExecutionSummaryPanel
from gui.execution_history_panel import ExecutionHistoryPanel

from app_logging.log_manager import save_execution_summary, get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
# Use the shared technical logger for main-window lifecycle and
# application-protection events.
logger = get_logger()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CONFIGURE MAIN WINDOW
        # ------------------------------------------------------------------
        self.setWindowTitle("DataAnonFramework")
        self.resize(900, 900)

        # ------------------------------------------------------------------
        # SECTION 3: CREATE APPLICATION MENU
        # ------------------------------------------------------------------
        file_menu = self.menuBar().addMenu("File")

        self.clear_action = QAction(
            "Clear / Start Afresh",
            self
        )

        self.clear_action.setShortcut("Ctrl+R")

        file_menu.addAction(
            self.clear_action
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE GUI PANELS
        # ------------------------------------------------------------------
        self.connection_panel = DatabaseConnectionPanel()
        self.source_panel = SourceTablePanel()
        self.rules_panel = AnonymizationRulesPanel()
        self.target_panel = TargetTablePanel()
        self.preview_panel = ValidationPreviewPanel()
        self.execution_panel = ExecutionPanel()
        self.summary_panel = ExecutionSummaryPanel()
        self.history_panel = ExecutionHistoryPanel()

        # ------------------------------------------------------------------
        # SECTION 5: CREATE MAIN WINDOW LAYOUT
        # ------------------------------------------------------------------
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.connection_panel)
        main_layout.addWidget(self.source_panel)
        main_layout.addWidget(self.rules_panel)
        main_layout.addWidget(self.target_panel)
        main_layout.addWidget(self.preview_panel)
        main_layout.addWidget(self.execution_panel)
        main_layout.addWidget(self.summary_panel)
        main_layout.addWidget(self.history_panel)

        # ------------------------------------------------------------------
        # SECTION 6: CREATE SCROLLABLE CENTRAL AREA
        # ------------------------------------------------------------------
        content_widget = QWidget()
        content_widget.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)

        self.setCentralWidget(scroll_area)

        # ------------------------------------------------------------------
        # SECTION 7: CONNECT GUI PANELS
        # ------------------------------------------------------------------
        # Successfully tested database configuration becomes available
        # to SourceTablePanel.
        self.connection_panel.connection_ready.connect(
            self.source_panel.set_connection_config
        )

        # Source metadata configures the target table.
        self.source_panel.columns_loaded.connect(
            self.target_panel.configure_from_source
        )

        # Loading a source table clears rules belonging to the previous table.
        self.source_panel.columns_loaded.connect(
            self.clear_previous_rules
        )

        # Selecting a source column updates datatype-compatible strategies.
        self.source_panel.column_list.itemSelectionChanged.connect(
            self.update_strategy_options
        )

        # Add Rule uses metadata for the selected source column.
        self.rules_panel.add_rule_button.clicked.connect(
            self.add_selected_rule
        )

        # Preview performs read-only validation and transformation.
        self.preview_panel.preview_button.clicked.connect(
            self.run_preview
        )

        # Execute starts the threaded OUT_PLACE anonymization.
        self.execution_panel.execute_button.clicked.connect(
            self.run_execution
        )

        # Process execution summaries and persist history.
        self.execution_panel.summary_ready.connect(
            self.handle_execution_summary
        )

        # Protect the GUI when execution starts/stops.
        self.execution_panel.execution_state_changed.connect(
            self.handle_execution_state
        )

        # Clear / Start Afresh resets the current working session.
        self.clear_action.triggered.connect(
            self.clear_application
        )

    def update_strategy_options(self):
        # ------------------------------------------------------------------
        # SECTION 8: UPDATE DATATYPE-AWARE STRATEGIES
        # ------------------------------------------------------------------
        column_info = self.source_panel.get_selected_column_info()

        self.rules_panel.configure_strategies(
            column_info
        )

    def add_selected_rule(self):
        # ------------------------------------------------------------------
        # SECTION 9: ADD RULE FOR SELECTED SOURCE COLUMN
        # ------------------------------------------------------------------
        column_info = self.source_panel.get_selected_column_info()

        self.rules_panel.add_rule(
            column_info
        )

    def clear_previous_rules(self, source_table, column_names):
        # ------------------------------------------------------------------
        # SECTION 10: CLEAR RULES AFTER SOURCE TABLE CHANGE
        # ------------------------------------------------------------------
        self.rules_panel.clear_rules()

    def run_preview(self):
        # ------------------------------------------------------------------
        # SECTION 11: COLLECT PREVIEW CONFIGURATION
        # ------------------------------------------------------------------
        connection_config = self.connection_panel.get_connection_config()
        source_config = self.source_panel.get_source_config()
        rules = self.rules_panel.get_rules()
        target_config = self.target_panel.get_target_config()

        # ------------------------------------------------------------------
        # SECTION 12: RUN PREVIEW
        # ------------------------------------------------------------------
        self.preview_panel.run_preview(
            connection_config,
            source_config,
            rules,
            target_config
        )

    def run_execution(self):
        # ------------------------------------------------------------------
        # SECTION 13: COLLECT EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        connection_config = self.connection_panel.get_connection_config()
        source_config = self.source_panel.get_source_config()
        rules = self.rules_panel.get_rules()
        target_config = self.target_panel.get_target_config()

        # ------------------------------------------------------------------
        # SECTION 14: START EXECUTION
        # ------------------------------------------------------------------
        self.execution_panel.run_execution(
            connection_config,
            source_config,
            rules,
            target_config
        )

    def handle_execution_state(self, running):
        # ------------------------------------------------------------------
        # SECTION 15: PROTECT GUI DURING ACTIVE EXECUTION
        # ------------------------------------------------------------------
        # While the worker is running, prevent configuration from changing.
        #
        # This avoids the GUI displaying a configuration different from
        # the configuration currently being processed by ExecutionWorker.
        configuration_enabled = not running

        self.connection_panel.setEnabled(
            configuration_enabled
        )

        self.source_panel.setEnabled(
            configuration_enabled
        )

        self.rules_panel.setEnabled(
            configuration_enabled
        )

        self.target_panel.setEnabled(
            configuration_enabled
        )

        self.preview_panel.setEnabled(
            configuration_enabled
        )

        # Clear / Start Afresh must also remain unavailable.
        self.clear_action.setEnabled(
            configuration_enabled
        )

        if running:
            logger.info(
                "GUI configuration controls locked during active execution."
            )
        else:
            logger.info(
                "GUI configuration controls unlocked after execution."
            )

    def handle_execution_summary(self, summary):
        # ------------------------------------------------------------------
        # SECTION 16: DISPLAY CURRENT EXECUTION SUMMARY
        # ------------------------------------------------------------------
        self.summary_panel.display_summary(
            summary
        )

        # ------------------------------------------------------------------
        # SECTION 17: SAVE EXECUTION HISTORY
        # ------------------------------------------------------------------
        save_successful = save_execution_summary(
            summary
        )

        # ------------------------------------------------------------------
        # SECTION 18: REFRESH EXECUTION HISTORY
        # ------------------------------------------------------------------
        self.history_panel.refresh_history()

        if not save_successful:
            self.history_panel.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.history_panel.status_label.setText(
                "Execution completed, but the history record could not be saved."
            )

    def clear_application(self):
        # ------------------------------------------------------------------
        # SECTION 19: PROTECT ACTIVE EXECUTION FROM RESET
        # ------------------------------------------------------------------
        # This check remains even though the menu action is disabled while
        # execution is active. It provides another safety layer.
        if self.execution_panel.is_execution_running():
            logger.warning(
                "Clear / Start Afresh request rejected because execution is running."
            )

            QMessageBox.warning(
                self,
                "Execution Running",
                "An anonymization execution is currently running.\n\n"
                "The application cannot be cleared until execution finishes."
            )

            return

        # ------------------------------------------------------------------
        # SECTION 20: CONFIRM APPLICATION RESET
        # ------------------------------------------------------------------
        answer = QMessageBox.question(
            self,
            "Start Afresh",
            "Clear all current selections and start afresh?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        # ------------------------------------------------------------------
        # SECTION 21: CLEAR CURRENT GUI SESSION
        # ------------------------------------------------------------------
        self.connection_panel.clear_panel()
        self.source_panel.clear_panel()
        self.rules_panel.clear_rules()
        self.target_panel.clear_panel()
        self.preview_panel.clear_preview()
        self.execution_panel.clear_panel()
        self.summary_panel.clear_summary()

        # Execution history is intentionally preserved.
        self.history_panel.refresh_history()

        logger.info(
            "Current DataAnonFramework GUI session cleared."
        )

    def closeEvent(self, event):
        # ------------------------------------------------------------------
        # SECTION 22: PROTECT ACTIVE QTHREAD DURING APPLICATION CLOSE
        # ------------------------------------------------------------------
        # Never allow MainWindow and its child QThread objects to be
        # destroyed while anonymization is still running.
        if self.execution_panel.is_execution_running():
            logger.warning(
                "Application close request rejected because anonymization "
                "execution is still running."
            )

            QMessageBox.warning(
                self,
                "Execution Running",
                "An anonymization execution is currently running.\n\n"
                "Please allow the execution to finish before closing "
                "DataAnonFramework."
            )

            # Ignore the operating-system/window-manager close request.
            event.ignore()

            return

        # ------------------------------------------------------------------
        # SECTION 23: ALLOW SAFE APPLICATION CLOSE
        # ------------------------------------------------------------------
        # No worker thread is active, therefore the window can close safely.
        logger.info(
            "DataAnonFramework main window closing."
        )

        event.accept()