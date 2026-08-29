"""
Module: app_style.py

Purpose:
Provides the shared visual styling for the Data Aninymization Engine GUI.

Main responsibilities:
- Provide consistent styling across the desktop application.
- Improve buttons, inputs, tables, section containers, and status areas.
- Create a clean professional appearance similar to the approved GUI mockup.
- Keep presentation rules separate from application logic.

This module does not access Oracle, perform anonymization, manage
transactions, or control application execution.
"""


def get_application_style():
    # ------------------------------------------------------------------
    # SECTION 1: APPLICATION STYLESHEET
    # ------------------------------------------------------------------
    # The design uses a clean Windows-style professional appearance.
    #
    # Functional status colors such as red errors and green success
    # messages can still be applied directly by individual GUI panels.
    return """

        /* ==============================================================
           GENERAL APPLICATION
           ============================================================== */

        QWidget {
            font-family: "Segoe UI";
            font-size: 10pt;
        }

        QMainWindow {
            background-color: #f5f7fa;
        }


        /* ==============================================================
           SECTION CONTAINERS
           ============================================================== */

        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #d8dde6;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 6px;
            color: #202124;
            background-color: #f5f7fa;
        }


        /* ==============================================================
           LABELS
           ============================================================== */

        QLabel {
            color: #202124;
            padding: 1px;
        }


        /* ==============================================================
           TEXT INPUTS
           ============================================================== */

        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #c7ccd4;
            border-radius: 4px;
            min-height: 26px;
            padding: 3px 7px;
            selection-background-color: #2f80d1;
        }

        QLineEdit:focus {
            border: 1px solid #2f80d1;
        }

        QLineEdit:disabled {
            background-color: #f1f3f5;
            color: #80868b;
        }


        /* ==============================================================
           COMBO BOXES
           ============================================================== */

        QComboBox {
            background-color: #ffffff;
            border: 1px solid #c7ccd4;
            border-radius: 4px;
            min-height: 26px;
            padding: 3px 7px;
        }

        QComboBox:focus {
            border: 1px solid #2f80d1;
        }

        QComboBox:disabled {
            background-color: #f1f3f5;
            color: #80868b;
        }

        QComboBox::drop-down {
            border: none;
            width: 24px;
        }


        /* ==============================================================
           STANDARD BUTTONS
           ============================================================== */

        QPushButton {
            background-color: #ffffff;
            border: 1px solid #aeb6c2;
            border-radius: 4px;
            min-height: 28px;
            padding: 4px 14px;
            color: #202124;
        }

        QPushButton:hover {
            background-color: #f3f6fa;
            border: 1px solid #7f8b9b;
        }

        QPushButton:pressed {
            background-color: #e7ebf0;
        }

        QPushButton:disabled {
            background-color: #f1f3f5;
            border: 1px solid #d5d9de;
            color: #9aa0a6;
        }


        /* ==============================================================
           PRIMARY ACTION BUTTON
           ============================================================== */

        QPushButton#primaryButton {
            background-color: #1976d2;
            border: 1px solid #1976d2;
            color: white;
            font-weight: bold;
            min-height: 30px;
        }

        QPushButton#primaryButton:hover {
            background-color: #1769ba;
        }

        QPushButton#primaryButton:pressed {
            background-color: #145da0;
        }

        QPushButton#primaryButton:disabled {
            background-color: #a9c7e8;
            border: 1px solid #a9c7e8;
            color: #eef4fb;
        }


        /* ==============================================================
           TABLES
           ============================================================== */

        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f8f9fb;
            border: 1px solid #d8dde6;
            border-radius: 4px;
            gridline-color: #e1e5ea;
            selection-background-color: #d8e9fb;
            selection-color: #202124;
        }

        QTableWidget::item {
            padding: 4px;
        }

        QTableWidget::item:selected {
            background-color: #d8e9fb;
            color: #202124;
        }

        QHeaderView::section {
            background-color: #f3f5f7;
            color: #202124;
            border: none;
            border-right: 1px solid #d8dde6;
            border-bottom: 1px solid #d8dde6;
            padding: 5px 7px;
            font-weight: bold;
        }


        /* ==============================================================
           LISTS
           ============================================================== */

        QListWidget {
            background-color: #ffffff;
            border: 1px solid #d8dde6;
            border-radius: 4px;
            padding: 2px;
        }

        QListWidget::item {
            padding: 4px;
        }

        QListWidget::item:selected {
            background-color: #d8e9fb;
            color: #202124;
        }


        /* ==============================================================
           EXECUTION SUMMARY / TEXT AREAS
           ============================================================== */

        QPlainTextEdit {
            background-color: #ffffff;
            border: 1px solid #d8dde6;
            border-radius: 4px;
            padding: 5px;
        }


        /* ==============================================================
           PROGRESS BAR
           ============================================================== */

        QProgressBar {
            background-color: #eef1f4;
            border: 1px solid #cdd3da;
            border-radius: 4px;
            min-height: 20px;
        }

        QProgressBar::chunk {
            background-color: #2f80d1;
            border-radius: 3px;
        }


        /* ==============================================================
           SCROLL BARS
           ============================================================== */

        QScrollBar:vertical {
            background-color: #f1f3f5;
            width: 12px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background-color: #c1c7cf;
            border-radius: 5px;
            min-height: 25px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #aab1bb;
        }

        QScrollBar:horizontal {
            background-color: #f1f3f5;
            height: 12px;
            margin: 0;
        }

        QScrollBar::handle:horizontal {
            background-color: #c1c7cf;
            border-radius: 5px;
            min-width: 25px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #aab1bb;
        }


        /* ==============================================================
           MENU BAR
           ============================================================== */

        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #d8dde6;
            padding: 2px;
        }

        QMenuBar::item {
            padding: 5px 9px;
            background: transparent;
        }

        QMenuBar::item:selected {
            background-color: #eef3f8;
            border-radius: 3px;
        }

        QMenu {
            background-color: #ffffff;
            border: 1px solid #d8dde6;
            padding: 4px;
        }

        QMenu::item {
            padding: 6px 24px 6px 10px;
        }

        QMenu::item:selected {
            background-color: #d8e9fb;
        }


        /* ==============================================================
           TOOL TIPS
           ============================================================== */

        QToolTip {
            background-color: #ffffff;
            color: #202124;
            border: 1px solid #aeb6c2;
            padding: 4px;
        }
    """