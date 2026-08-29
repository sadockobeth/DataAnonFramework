"""
Module: main_window.py

Purpose:
Assembles and coordinates the main Data Anonymization Engine GUI window.

Main responsibilities:
- Create and display the major GUI panels.
- Organize the application into clearly numbered workflow sections.
- Display the centralized application name and version.
- Provide File and Help application menus.
- Display application information through a custom About dialog.
- Display the company logo as the application window icon.
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

from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QGroupBox,
    QFrame,
    QMessageBox
)

from app_info import APP_NAME, APP_VERSION

from gui.about_dialog import AboutDialog
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
logger = get_logger()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CONFIGURE MAIN WINDOW
        # ------------------------------------------------------------------
        self.setWindowTitle(
            f"{APP_NAME} - Version {APP_VERSION}"
        )

        # Keep the established application window size.
        self.resize(900, 800)

        # ------------------------------------------------------------------
        # SECTION 3: CONFIGURE APPLICATION WINDOW ICON
        # ------------------------------------------------------------------
        # Use the same company logo used by AboutDialog.
        project_root = Path(__file__).resolve().parent.parent
        logo_path = project_root / "assets" / "bot_logo.png"

        if logo_path.exists():
            self.setWindowIcon(
                QIcon(str(logo_path))
            )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE FILE MENU
        # ------------------------------------------------------------------
        file_menu = self.menuBar().addMenu(
            "File"
        )

        self.clear_action = QAction(
            "Clear / Start Afresh",
            self
        )

        self.clear_action.setShortcut(
            "Ctrl+R"
        )

        file_menu.addAction(
            self.clear_action
        )

        # ------------------------------------------------------------------
        # SECTION 5: CREATE HELP MENU
        # ------------------------------------------------------------------
        help_menu = self.menuBar().addMenu(
            "Help"
        )

        self.about_action = QAction(
            f"About {APP_NAME}",
            self
        )

        help_menu.addAction(
            self.about_action
        )

        # ------------------------------------------------------------------
        # SECTION 6: CREATE GUI PANELS
        # ------------------------------------------------------------------
        # These are the existing functional panels.
        #
        # Their internal behavior remains unchanged. MainWindow only
        # coordinates them and controls how they are presented.
        self.connection_panel = DatabaseConnectionPanel()
        self.source_panel = SourceTablePanel()
        self.rules_panel = AnonymizationRulesPanel()
        self.target_panel = TargetTablePanel()
        self.preview_panel = ValidationPreviewPanel()
        self.execution_panel = ExecutionPanel()
        self.summary_panel = ExecutionSummaryPanel()
        self.history_panel = ExecutionHistoryPanel()

        # ------------------------------------------------------------------
        # SECTION 7: CREATE NUMBERED WORKFLOW SECTIONS
        # ------------------------------------------------------------------
        # Each existing panel is wrapped inside a QGroupBox.
        #
        # This gives the application a clear visual workflow while leaving
        # the actual panel functionality unchanged.
        self.connection_section = self.create_section_group(
            "1. Database Connection",
            self.connection_panel
        )

        self.source_section = self.create_section_group(
            "2. Source Data",
            self.source_panel
        )

        self.rules_section = self.create_section_group(
            "3. Anonymization Rules",
            self.rules_panel
        )

        self.target_section = self.create_section_group(
            "4. Target Data",
            self.target_panel
        )

        self.preview_section = self.create_section_group(
            "5. Validate and Preview",
            self.preview_panel
        )

        self.execution_section = self.create_section_group(
            "6. Execute Anonymization",
            self.execution_panel
        )

        self.summary_section = self.create_section_group(
            "7. Execution Summary",
            self.summary_panel
        )

        self.history_section = self.create_section_group(
            "8. Execution History",
            self.history_panel
        )

        # ------------------------------------------------------------------
        # SECTION 8: CREATE MAIN WINDOW LAYOUT
        # ------------------------------------------------------------------
        # Arrange the workflow sections vertically in the same order that
        # the user follows when preparing and running anonymization.
        main_layout = QVBoxLayout()

        # Keep spacing compact but visually separated.
        main_layout.setContentsMargins(
            12,
            8,
            12,
            12
        )

        main_layout.setSpacing(
            8
        )

        main_layout.addWidget(
            self.connection_section
        )

        main_layout.addWidget(
            self.source_section
        )

        main_layout.addWidget(
            self.rules_section
        )

        main_layout.addWidget(
            self.target_section
        )

        main_layout.addWidget(
            self.preview_section
        )

        main_layout.addWidget(
            self.execution_section
        )

        main_layout.addWidget(
            self.summary_section
        )

        main_layout.addWidget(
            self.history_section
        )

        # ------------------------------------------------------------------
        # SECTION 9: CREATE SCROLLABLE CENTRAL AREA
        # ------------------------------------------------------------------
        # The application retains the normal 900 x 800 window while the
        # complete workflow remains accessible through vertical scrolling.
        content_widget = QWidget()

        content_widget.setLayout(
            main_layout
        )

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        # Remove the default heavy scroll-area border because the numbered
        # group boxes already provide the visual section boundaries.
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setWidget(
            content_widget
        )

        self.setCentralWidget(
            scroll_area
        )

        # ------------------------------------------------------------------
        # SECTION 10: CONNECT GUI PANELS
        # ------------------------------------------------------------------
        # A successfully tested database connection becomes available
        # to the source-table panel.
        self.connection_panel.connection_ready.connect(
            self.source_panel.set_connection_config
        )

        # Loaded source metadata configures the target-table panel.
        self.source_panel.columns_loaded.connect(
            self.target_panel.configure_from_source
        )

        # Changing source table invalidates previous anonymization rules.
        self.source_panel.columns_loaded.connect(
            self.clear_previous_rules
        )

        # Selecting a source column updates allowed anonymization methods
        # according to the Oracle datatype.
        self.source_panel.column_list.itemSelectionChanged.connect(
            self.update_strategy_options
        )

        # Add the selected anonymization rule.
        self.rules_panel.add_rule_button.clicked.connect(
            self.add_selected_rule
        )

        # Validate configuration and display sample anonymization results.
        self.preview_panel.preview_button.clicked.connect(
            self.run_preview
        )

        # Start full anonymization execution.
        self.execution_panel.execute_button.clicked.connect(
            self.run_execution
        )

        # Receive completed execution summary.
        self.execution_panel.summary_ready.connect(
            self.handle_execution_summary
        )

        # Lock or unlock configuration controls while execution runs.
        self.execution_panel.execution_state_changed.connect(
            self.handle_execution_state
        )

        # File menu actions.
        self.clear_action.triggered.connect(
            self.clear_application
        )

        # Help menu actions.
        self.about_action.triggered.connect(
            self.show_about
        )

    def create_section_group(
        self,
        title,
        panel
    ):
        # ------------------------------------------------------------------
        # SECTION 11: CREATE WORKFLOW SECTION
        # ------------------------------------------------------------------
        # Wrap an existing functional panel inside a clearly labelled
        # QGroupBox.
        #
        # The panel itself remains unchanged. This method affects only
        # presentation and workflow organization.
        group_box = QGroupBox(
            title
        )

        group_layout = QVBoxLayout()

        # Keep enough internal spacing for the section to remain clean
        # without wasting excessive screen space.
        group_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        group_layout.setSpacing(
            4
        )

        group_layout.addWidget(
            panel
        )

        group_box.setLayout(
            group_layout
        )

        return group_box

    def update_strategy_options(self):
        # ------------------------------------------------------------------
        # SECTION 12: UPDATE DATATYPE-AWARE STRATEGIES
        # ------------------------------------------------------------------
        column_info = self.source_panel.get_selected_column_info()

        self.rules_panel.configure_strategies(
            column_info
        )

    def add_selected_rule(self):
        # ------------------------------------------------------------------
        # SECTION 13: ADD RULE FOR SELECTED SOURCE COLUMN
        # ------------------------------------------------------------------
        column_info = self.source_panel.get_selected_column_info()

        self.rules_panel.add_rule(
            column_info
        )

    def clear_previous_rules(
        self,
        source_table,
        column_names
    ):
        # ------------------------------------------------------------------
        # SECTION 14: CLEAR RULES AFTER SOURCE TABLE CHANGE
        # ------------------------------------------------------------------
        self.rules_panel.clear_rules()

    def run_preview(self):
        # ------------------------------------------------------------------
        # SECTION 15: COLLECT PREVIEW CONFIGURATION
        # ------------------------------------------------------------------
        connection_config = self.connection_panel.get_connection_config()
        source_config = self.source_panel.get_source_config()
        rules = self.rules_panel.get_rules()
        target_config = self.target_panel.get_target_config()

        # ------------------------------------------------------------------
        # SECTION 16: RUN PREVIEW
        # ------------------------------------------------------------------
        self.preview_panel.run_preview(
            connection_config,
            source_config,
            rules,
            target_config
        )

    def run_execution(self):
        # ------------------------------------------------------------------
        # SECTION 17: COLLECT EXECUTION CONFIGURATION
        # ------------------------------------------------------------------
        connection_config = self.connection_panel.get_connection_config()
        source_config = self.source_panel.get_source_config()
        rules = self.rules_panel.get_rules()
        target_config = self.target_panel.get_target_config()

        # ------------------------------------------------------------------
        # SECTION 18: START EXECUTION
        # ------------------------------------------------------------------
        self.execution_panel.run_execution(
            connection_config,
            source_config,
            rules,
            target_config
        )

    def handle_execution_state(
        self,
        running
    ):
        # ------------------------------------------------------------------
        # SECTION 19: PROTECT GUI DURING ACTIVE EXECUTION
        # ------------------------------------------------------------------
        # Configuration controls are disabled while anonymization executes.
        #
        # ExecutionPanel itself remains enabled because its Cancel button
        # must continue to work during execution.
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

    def handle_execution_summary(
        self,
        summary
    ):
        # ------------------------------------------------------------------
        # SECTION 20: DISPLAY EXECUTION SUMMARY
        # ------------------------------------------------------------------
        self.summary_panel.display_summary(
            summary
        )

        # ------------------------------------------------------------------
        # SECTION 21: SAVE EXECUTION HISTORY
        # ------------------------------------------------------------------
        save_successful = save_execution_summary(
            summary
        )

        # ------------------------------------------------------------------
        # SECTION 22: REFRESH EXECUTION HISTORY
        # ------------------------------------------------------------------
        self.history_panel.refresh_history()

        if not save_successful:
            self.history_panel.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.history_panel.status_label.setText(
                "Execution completed, but the history record could not be saved."
            )

    def show_about(self):
        # ------------------------------------------------------------------
        # SECTION 23: DISPLAY CUSTOM ABOUT DIALOG
        # ------------------------------------------------------------------
        # The custom dialog provides more flexibility than QMessageBox.about()
        # and allows the company logo to be displayed.
        about_dialog = AboutDialog(
            self
        )

        about_dialog.exec()

    def clear_application(self):
        # ------------------------------------------------------------------
        # SECTION 24: PROTECT ACTIVE EXECUTION FROM RESET
        # ------------------------------------------------------------------
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
        # SECTION 25: CONFIRM APPLICATION RESET
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
        # SECTION 26: CLEAR CURRENT GUI SESSION
        # ------------------------------------------------------------------
        self.connection_panel.clear_panel()
        self.source_panel.clear_panel()
        self.rules_panel.clear_rules()
        self.target_panel.clear_panel()
        self.preview_panel.clear_preview()
        self.execution_panel.clear_panel()
        self.summary_panel.clear_summary()

        # Execution history is deliberately preserved.
        self.history_panel.refresh_history()

        logger.info(
            "Current %s GUI session cleared.",
            APP_NAME
        )

    def closeEvent(
        self,
        event
    ):
        # ------------------------------------------------------------------
        # SECTION 27: PROTECT ACTIVE THREAD DURING APPLICATION CLOSE
        # ------------------------------------------------------------------
        if self.execution_panel.is_execution_running():
            logger.warning(
                "Application close request rejected because anonymization "
                "execution is still running."
            )

            QMessageBox.warning(
                self,
                "Execution Running",
                "An anonymization execution is currently running.\n\n"
                f"Please allow the execution to finish before closing {APP_NAME}."
            )

            event.ignore()

            return

        # ------------------------------------------------------------------
        # SECTION 28: ALLOW SAFE APPLICATION CLOSE
        # ------------------------------------------------------------------
        logger.info(
            "%s main window closing.",
            APP_NAME
        )

        event.accept()