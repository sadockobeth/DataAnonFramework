"""
Module: execution_history_panel.py

Purpose:
Displays recent anonymization execution history in the DataAnonFramework GUI.

Main responsibilities:
- Load persistent execution records from app_logging/log_manager.py.
- Display recent execution status, source, target, row count, start time, and duration.
- Allow the user to refresh the execution-history display manually.
- Keep historical execution information separate from the current execution summary.

This module does not execute anonymization, access Oracle, store
database credentials, or write execution-history files directly.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView
)

from app_logging.log_manager import load_execution_history


class ExecutionHistoryPanel(QWidget):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: CREATE EXECUTION HISTORY TABLE
        # ------------------------------------------------------------------
        # QTableWidget displays one anonymization execution per row.
        self.history_table = QTableWidget()

        # Six columns provide the most useful summary information
        # without making the table unnecessarily wide.
        self.history_table.setColumnCount(6)

        self.history_table.setHorizontalHeaderLabels([
            "Status",
            "Source",
            "Target",
            "Rows",
            "Started",
            "Duration"
        ])

        # Provide enough vertical space to display several execution records.
        self.history_table.setMinimumHeight(200)

        # Prevent direct editing because execution history is read-only.
        self.history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Select complete rows instead of individual cells.
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        # ------------------------------------------------------------------
        # SECTION 2: CREATE REFRESH BUTTON
        # ------------------------------------------------------------------
        # Allows execution history to be reloaded manually from disk.
        self.refresh_button = QPushButton("Refresh Execution History")

        # ------------------------------------------------------------------
        # SECTION 3: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # Displays the number of records loaded or any history-related message.
        self.status_label = QLabel("Execution history not yet loaded.")

        # ------------------------------------------------------------------
        # SECTION 4: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout places the heading, history table, refresh button,
        # and status message vertically.
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Execution History:"))
        layout.addWidget(self.history_table)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 5: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        # Reload execution history whenever the user clicks Refresh.
        self.refresh_button.clicked.connect(self.refresh_history)

        # Load existing execution history when this panel is created.
        self.refresh_history()

    def refresh_history(self):
        # ------------------------------------------------------------------
        # SECTION 6: LOAD EXECUTION HISTORY
        # ------------------------------------------------------------------
        # Retrieve the most recent execution records from the persistent
        # execution_history.jsonl file.
        history = load_execution_history(limit=50)

        # Remove previous table contents before displaying refreshed history.
        self.history_table.clearContents()
        self.history_table.setRowCount(len(history))

        # ------------------------------------------------------------------
        # SECTION 7: DISPLAY EXECUTION HISTORY
        # ------------------------------------------------------------------
        # Each execution record becomes one row in the GUI table.
        for row_number, record in enumerate(history):

            # Convert the stored ISO timestamp back into a datetime object.
            started_at = datetime.fromisoformat(record["started_at"])

            # Convert execution duration into HH:MM:SS format.
            duration = self.format_duration(record["duration_seconds"])

            self.history_table.setItem(
                row_number,
                0,
                QTableWidgetItem(record["status"])
            )

            self.history_table.setItem(
                row_number,
                1,
                QTableWidgetItem(record["source"])
            )

            self.history_table.setItem(
                row_number,
                2,
                QTableWidgetItem(record["target"])
            )

            self.history_table.setItem(
                row_number,
                3,
                QTableWidgetItem(f'{record["rows_processed"]:,}')
            )

            self.history_table.setItem(
                row_number,
                4,
                QTableWidgetItem(
                    started_at.strftime("%d-%b-%Y %H:%M:%S")
                )
            )

            self.history_table.setItem(
                row_number,
                5,
                QTableWidgetItem(duration)
            )

        # Resize columns according to their current contents.
        self.history_table.resizeColumnsToContents()

        # ------------------------------------------------------------------
        # SECTION 8: UPDATE HISTORY STATUS
        # ------------------------------------------------------------------
        if history:
            self.status_label.setStyleSheet("")
            self.status_label.setText(
                f"{len(history)} execution history record(s) loaded."
            )
        else:
            self.status_label.setStyleSheet("")
            self.status_label.setText(
                "No execution history recorded yet."
            )

    def format_duration(self, duration_seconds):
        # ------------------------------------------------------------------
        # SECTION 9: FORMAT EXECUTION DURATION
        # ------------------------------------------------------------------
        # Convert total execution seconds into HH:MM:SS.
        total_seconds = int(duration_seconds)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"