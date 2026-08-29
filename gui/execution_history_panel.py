"""
Module: execution_history_panel.py

Purpose:
Displays recent anonymization execution history in the GUI.

Main responsibilities:
- Load recent execution summaries from persistent execution history.
- Display SUCCESS, FAILED, and CANCELLED executions.
- Display source table, target table, processed rows, start time, and duration.
- Show the most recent executions first.
- Allow execution history to be refreshed manually.
- Report history-loading errors clearly.
- Keep execution history separate from the current application session.

This module does not execute anonymization, access Oracle, save execution
history, delete history records, or modify execution summaries.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)

from app_logging.log_manager import load_execution_history
from reporting.execution_summary import format_duration


class ExecutionHistoryPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: CREATE HISTORY DESCRIPTION
        # ------------------------------------------------------------------
        self.description_label = QLabel(
            "Review recent anonymization executions recorded by the application."
        )

        # ------------------------------------------------------------------
        # SECTION 2: CREATE REFRESH BUTTON
        # ------------------------------------------------------------------
        self.refresh_button = QPushButton(
            "Refresh Execution History"
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE EXECUTION HISTORY TABLE
        # ------------------------------------------------------------------
        self.history_table = QTableWidget()

        self.history_table.setColumnCount(
            6
        )

        self.history_table.setHorizontalHeaderLabels([
            "Status",
            "Source",
            "Target",
            "Rows",
            "Started",
            "Duration"
        ])

        # History is informational only.
        self.history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Selecting a row is clearer than selecting individual cells.
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.history_table.setAlternatingRowColors(
            True
        )

        # Row numbers are not useful for execution history.
        self.history_table.verticalHeader().setVisible(
            False
        )

        self.history_table.setMinimumHeight(
            220
        )

        # ------------------------------------------------------------------
        # SECTION 4: CONFIGURE TABLE COLUMN WIDTHS
        # ------------------------------------------------------------------
        header = self.history_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # ------------------------------------------------------------------
        # SECTION 5: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Execution history has not been loaded."
        )

        # ------------------------------------------------------------------
        # SECTION 6: CREATE TOP ACTION ROW
        # ------------------------------------------------------------------
        action_layout = QHBoxLayout()

        action_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        action_layout.setSpacing(
            8
        )

        action_layout.addWidget(
            self.description_label
        )

        action_layout.addStretch()

        action_layout.addWidget(
            self.refresh_button
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE PANEL LAYOUT
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
            6
        )

        layout.addLayout(
            action_layout
        )

        layout.addWidget(
            self.history_table
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(
            layout
        )

        # ------------------------------------------------------------------
        # SECTION 8: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        self.refresh_button.clicked.connect(
            self.refresh_history
        )

        # ------------------------------------------------------------------
        # SECTION 9: LOAD HISTORY WHEN PANEL IS CREATED
        # ------------------------------------------------------------------
        self.refresh_history()

    def refresh_history(self):
        # ------------------------------------------------------------------
        # SECTION 10: PREPARE HISTORY REFRESH
        # ------------------------------------------------------------------
        self.history_table.setRowCount(
            0
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Loading execution history..."
        )

        try:
            # ------------------------------------------------------------------
            # SECTION 11: LOAD RECENT EXECUTION HISTORY
            # ------------------------------------------------------------------
            # Keep the GUI focused on recent executions rather than loading
            # an unlimited number of historical records.
            history = load_execution_history(
                limit=50
            )

            # ------------------------------------------------------------------
            # SECTION 12: HANDLE EMPTY HISTORY
            # ------------------------------------------------------------------
            if not history:
                self.status_label.setStyleSheet("")

                self.status_label.setText(
                    "No execution history is available."
                )

                return

            # ------------------------------------------------------------------
            # SECTION 13: CONFIGURE TABLE ROWS
            # ------------------------------------------------------------------
            self.history_table.setRowCount(
                len(history)
            )

            # ------------------------------------------------------------------
            # SECTION 14: DISPLAY HISTORY RECORDS
            # ------------------------------------------------------------------
            # load_execution_history() already returns newest records first.
            for row, summary in enumerate(history):

                status = str(
                    summary.get(
                        "status",
                        "UNKNOWN"
                    )
                ).upper()

                source = str(
                    summary.get(
                        "source",
                        ""
                    )
                )

                target = str(
                    summary.get(
                        "target",
                        ""
                    )
                )

                rows_processed = summary.get(
                    "rows_processed",
                    0
                )

                started_at = self.format_started_at(
                    summary.get(
                        "started_at"
                    )
                )

                duration = format_duration(
                    summary.get(
                        "duration_seconds"
                    )
                )

                # ----------------------------------------------------------
                # STATUS
                # ----------------------------------------------------------
                status_item = QTableWidgetItem(
                    status
                )

                # ----------------------------------------------------------
                # SOURCE
                # ----------------------------------------------------------
                source_item = QTableWidgetItem(
                    source
                )

                # ----------------------------------------------------------
                # TARGET
                # ----------------------------------------------------------
                target_item = QTableWidgetItem(
                    target
                )

                # ----------------------------------------------------------
                # ROWS
                # ----------------------------------------------------------
                try:
                    rows_text = f"{int(rows_processed):,}"
                except (TypeError, ValueError):
                    rows_text = str(
                        rows_processed
                    )

                rows_item = QTableWidgetItem(
                    rows_text
                )

                rows_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight |
                    Qt.AlignmentFlag.AlignVCenter
                )

                # ----------------------------------------------------------
                # STARTED
                # ----------------------------------------------------------
                started_item = QTableWidgetItem(
                    started_at
                )

                # ----------------------------------------------------------
                # DURATION
                # ----------------------------------------------------------
                duration_item = QTableWidgetItem(
                    duration
                )

                # ----------------------------------------------------------
                # ADD VALUES TO TABLE
                # ----------------------------------------------------------
                self.history_table.setItem(
                    row,
                    0,
                    status_item
                )

                self.history_table.setItem(
                    row,
                    1,
                    source_item
                )

                self.history_table.setItem(
                    row,
                    2,
                    target_item
                )

                self.history_table.setItem(
                    row,
                    3,
                    rows_item
                )

                self.history_table.setItem(
                    row,
                    4,
                    started_item
                )

                self.history_table.setItem(
                    row,
                    5,
                    duration_item
                )

            # ------------------------------------------------------------------
            # SECTION 15: REPORT SUCCESS
            # ------------------------------------------------------------------
            self.status_label.setStyleSheet("")

            self.status_label.setText(
                f"Showing {len(history)} most recent execution record(s)."
            )

        except Exception as error:
            # ------------------------------------------------------------------
            # SECTION 16: HANDLE HISTORY-LOADING FAILURE
            # ------------------------------------------------------------------
            self.history_table.setRowCount(
                0
            )

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Unable to load execution history: {error}"
            )

    def format_started_at(
        self,
        started_at
    ):
        # ------------------------------------------------------------------
        # SECTION 17: FORMAT EXECUTION START TIME
        # ------------------------------------------------------------------
        if not started_at:
            return "N/A"

        # Execution summaries currently use ISO format:
        #
        # 2026-08-30T21:30:20
        #
        # Displaying a space instead of T is easier for business users:
        #
        # 2026-08-30 21:30:20
        return str(
            started_at
        ).replace(
            "T",
            " "
        )