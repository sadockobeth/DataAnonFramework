"""
Module: execution_summary_panel.py

Purpose:
Displays the result of the most recent anonymization execution.

Main responsibilities:
- Receive an execution summary from MainWindow.
- Display SUCCESS, FAILED, or CANCELLED status clearly.
- Display source and target information.
- Display row, batch, timing, rule, and exclusion information.
- Display execution failure information when applicable.
- Present summary information in a read-only format.
- Clear the current execution summary when starting a new session.

This module does not execute anonymization, access Oracle, persist
execution history, or create execution summaries.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit
)

from reporting.execution_summary import format_execution_summary


class ExecutionSummaryPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "No execution summary available."
        )

        # ------------------------------------------------------------------
        # SECTION 2: CREATE SUMMARY DISPLAY
        # ------------------------------------------------------------------
        self.summary_display = QPlainTextEdit()

        self.summary_display.setReadOnly(
            True
        )

        self.summary_display.setMinimumHeight(
            250
        )

        self.summary_display.setPlaceholderText(
            "The result of the most recent anonymization execution "
            "will appear here."
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's numbered QGroupBox provides the outer spacing.
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            6
        )

        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.summary_display
        )

        self.setLayout(
            layout
        )

    def display_summary(
        self,
        summary
    ):
        # ------------------------------------------------------------------
        # SECTION 4: VALIDATE SUMMARY
        # ------------------------------------------------------------------
        if not summary:
            self.clear_summary()
            return

        # ------------------------------------------------------------------
        # SECTION 5: DISPLAY FORMATTED SUMMARY
        # ------------------------------------------------------------------
        formatted_summary = format_execution_summary(
            summary
        )

        self.summary_display.setPlainText(
            formatted_summary
        )

        # Always position the summary at the beginning after loading it.
        cursor = self.summary_display.textCursor()
        cursor.movePosition(
            cursor.MoveOperation.Start
        )

        self.summary_display.setTextCursor(
            cursor
        )

        # ------------------------------------------------------------------
        # SECTION 6: DISPLAY SUMMARY STATUS
        # ------------------------------------------------------------------
        status = str(
            summary.get(
                "status",
                "UNKNOWN"
            )
        ).upper()

        if status == "SUCCESS":
            self.status_label.setStyleSheet(
                "color: green; font-weight: bold;"
            )

            self.status_label.setText(
                "✓ Execution completed successfully."
            )

        elif status == "CANCELLED":
            self.status_label.setStyleSheet(
                "color: #b26a00; font-weight: bold;"
            )

            self.status_label.setText(
                "Execution was cancelled."
            )

        elif status == "FAILED":
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Execution failed."
            )

        else:
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Execution status: {status}"
            )

    def clear_summary(self):
        # ------------------------------------------------------------------
        # SECTION 7: CLEAR EXECUTION SUMMARY
        # ------------------------------------------------------------------
        self.summary_display.clear()

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "No execution summary available."
        )