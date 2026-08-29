"""
Module: app_style.py

Purpose:
Provides the shared visual styling for the Data Aninymization Engine GUI.

Main responsibilities:
- Provide consistent fonts, spacing, buttons, inputs, tables, and menus.
- Improve readability without changing application functionality.
- Keep GUI presentation rules separate from application logic.

This module does not access Oracle, perform anonymization, or manage
application execution.
"""


def get_application_style():
    # ------------------------------------------------------------------
    # SECTION 1: RETURN APPLICATION STYLESHEET
    # ------------------------------------------------------------------
    # The stylesheet is intentionally simple and uses standard Qt colors
    # so the application remains clear and professional.
    return """
        QWidget {
            font-size: 10pt;
        }

        QMainWindow {
            background-color: palette(window);
        }

        QLabel {
            padding: 2px;
        }

        QLineEdit,
        QComboBox {
            min-height: 26px;
            padding: 3px 6px;
        }

        QPushButton {
            min-height: 28px;
            padding: 4px 10px;
        }

        QPushButton:disabled {
            color: gray;
        }

        QListWidget,
        QTableWidget,
        QPlainTextEdit {
            border: 1px solid palette(mid);
        }

        QHeaderView::section {
            padding: 5px;
            font-weight: bold;
        }

        QProgressBar {
            min-height: 20px;
        }

        QMenuBar {
            padding: 2px;
        }

        QMenu {
            padding: 4px;
        }
    """