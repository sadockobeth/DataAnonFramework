"""
Module: execution_summary_panel.py

Purpose:
Displays the result of an anonymization execution in the GUI.

Main responsibilities:
- Receive a structured execution summary from ExecutionPanel.
- Format the summary using reporting/execution_summary.py.
- Display execution statistics, rules, exclusions, timestamps, and status.
- Display failed execution information when available.
- Clear the previous summary when starting a new session.

This module does not execute anonymization, access Oracle, or build
execution statistics itself.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit

from reporting.execution_summary import format_execution_summary


class ExecutionSummaryPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: CREATE SUMMARY DISPLAY
        # ------------------------------------------------------------------
        # QPlainTextEdit provides a multi-line area suitable for displaying
        # structured execution information.
        self.summary_display = QPlainTextEdit()

        # The execution report is informational and should not be editable.
        self.summary_display.setReadOnly(True)

        # Keep enough vertical space to display useful summary information.
        self.summary_display.setMinimumHeight(250)

        # ------------------------------------------------------------------
        # SECTION 2: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout places the heading above the execution summary.
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Execution Summary:"))
        layout.addWidget(self.summary_display)
        self.setLayout(layout)

    def display_summary(self, summary):
        # ------------------------------------------------------------------
        # SECTION 3: DISPLAY EXECUTION SUMMARY
        # ------------------------------------------------------------------
        # Convert the structured summary dictionary into readable text.
        summary_text = format_execution_summary(summary)
        self.summary_display.setPlainText(summary_text)

    def clear_summary(self):
        # ------------------------------------------------------------------
        # SECTION 4: CLEAR EXECUTION SUMMARY
        # ------------------------------------------------------------------
        # Remove the previous execution report when the user chooses
        # File -> Clear / Start Afresh.
        self.summary_display.clear()