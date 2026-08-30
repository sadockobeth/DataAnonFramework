"""
Module: app_style.py

Purpose:
Provides the centralized visual styling for the Data Aninymization Engine GUI.

Main responsibilities:
- Define consistent application fonts, backgrounds, and spacing.
- Style numbered application sections.
- Style input fields and combo boxes.
- Style standard application buttons.
- Provide blue-outline action buttons.
- Provide a strong filled-blue execution button.
- Style tables, lists, progress bars, menus, and scrollbars.
- Keep the visual appearance consistent across all GUI sections.

This module contains presentation styling only and does not contain
application logic, database access, or anonymization functionality.
"""


# ------------------------------------------------------------------
# SECTION 1: APPLICATION STYLESHEET
# ------------------------------------------------------------------
APP_STYLE = """

/* ==================================================================
   APPLICATION
   ================================================================== */

QMainWindow {
    background-color: #f4f6f8;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #202124;
}


/* ==================================================================
   MENU BAR
   ================================================================== */

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #d8dde3;
    padding: 3px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #eef5fb;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #cfd6dd;
    padding: 4px;
}

QMenu::item {
    padding: 7px 28px 7px 10px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #eaf4fc;
}


/* ==================================================================
   NUMBERED SECTION GROUPS
   ================================================================== */

QGroupBox {
    background-color: #ffffff;

    border: 1px solid #d8dde3;
    border-radius: 8px;

    margin-top: 13px;

    padding-top: 12px;

    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;

    left: 12px;

    padding: 0 6px;

    color: #263238;

    background-color: #ffffff;
}


/* ==================================================================
   LABELS
   ================================================================== */

QLabel {
    background-color: transparent;
    color: #30363b;
}


/* ==================================================================
   TEXT INPUTS
   ================================================================== */

QLineEdit {
    background-color: #ffffff;

    border: 1px solid #bfc7cf;
    border-radius: 6px;

    padding: 6px 8px;

    min-height: 22px;

    selection-background-color: #cfe7f8;
}

QLineEdit:hover {
    border-color: #8fa9bd;
}

QLineEdit:focus {
    border: 1px solid #4a9ed8;
}

QLineEdit:read-only {
    background-color: #f6f7f8;
    color: #555b60;
}

QLineEdit:disabled {
    background-color: #f0f1f2;
    color: #999999;
    border-color: #d4d7da;
}


/* ==================================================================
   COMBO BOXES
   ================================================================== */

QComboBox {
    background-color: #ffffff;

    border: 1px solid #bfc7cf;
    border-radius: 6px;

    padding: 6px 8px;

    min-height: 22px;
}

QComboBox:hover {
    border-color: #8fa9bd;
}

QComboBox:focus {
    border: 1px solid #4a9ed8;
}

QComboBox:disabled {
    background-color: #f0f1f2;
    color: #999999;
    border-color: #d4d7da;
}

QComboBox::drop-down {
    border: none;

    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;

    border: 1px solid #c7cdd3;

    selection-background-color: #e8f3fb;
    selection-color: #202124;

    outline: none;
}


/* ==================================================================
   STANDARD BUTTON
   ================================================================== */

/*
All ordinary buttons use a clean neutral appearance.

Examples:
- Remove Rule
- Remove Exclusion
- Cancel Execution
*/

QPushButton {
    background-color: #ffffff;

    color: #252a2e;

    border: 1px solid #b9c1c8;
    border-radius: 7px;

    padding: 7px 16px;

    min-height: 24px;

    font-weight: 600;
}

QPushButton:hover {
    background-color: #f5f7f8;
    border-color: #929da6;
}

QPushButton:pressed {
    background-color: #e9edef;
    border-color: #78848d;
}

QPushButton:disabled {
    background-color: #f3f4f5;

    color: #a1a5a8;

    border-color: #d4d7da;
}


/* ==================================================================
   BLUE OUTLINE ACTION BUTTON
   ================================================================== */

/*
primaryButton is deliberately an outline button.

This produces the appearance similar to the Load Columns button
reference:

    white / very light background
    blue border
    dark text
    rounded corners

Use for:
- Test Connection
- Load Columns
- Add Rule
- Add Exclusion
- Validate and Preview
*/

QPushButton#primaryButton {
    background-color: #ffffff;

    color: #202124;

    border: 2px solid #55a8e4;
    border-radius: 8px;

    padding: 7px 18px;

    min-height: 24px;

    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #f1f8fd;

    border-color: #268fd3;
}

QPushButton#primaryButton:pressed {
    background-color: #e3f1fb;

    border-color: #1979b8;
}

QPushButton#primaryButton:focus {
    border: 2px solid #3398dc;
}

QPushButton#primaryButton:disabled {
    background-color: #f4f5f6;

    color: #a1a5a8;

    border-color: #c9ced3;
}


/* ==================================================================
   EXECUTE BUTTON
   ================================================================== */

/*
Execute Anonymization is deliberately stronger than the other
workflow buttons because it performs the final database operation.
*/

QPushButton#executeButton {
    background-color: #2f8fd3;

    color: #ffffff;

    border: 1px solid #2f8fd3;
    border-radius: 8px;

    padding: 8px 20px;

    min-height: 25px;

    font-weight: 600;
}

QPushButton#executeButton:hover {
    background-color: #247fc0;

    border-color: #247fc0;
}

QPushButton#executeButton:pressed {
    background-color: #1d6fa9;

    border-color: #1d6fa9;
}

QPushButton#executeButton:disabled {
    background-color: #b6cbd9;

    color: #f1f1f1;

    border-color: #b6cbd9;
}


/* ==================================================================
   TABLES
   ================================================================== */

QTableWidget {
    background-color: #ffffff;

    alternate-background-color: #f8fafb;

    border: 1px solid #d5dbe0;
    border-radius: 5px;

    gridline-color: #e1e5e8;

    selection-background-color: #dceefa;
    selection-color: #202124;

    outline: none;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #dceefa;
    color: #202124;
}

QHeaderView::section {
    background-color: #edf2f5;

    color: #30363b;

    border: none;
    border-right: 1px solid #d5dbe0;
    border-bottom: 1px solid #d5dbe0;

    padding: 6px;

    font-weight: 600;
}


/* ==================================================================
   LISTS
   ================================================================== */

QListWidget {
    background-color: #ffffff;

    alternate-background-color: #f8fafb;

    border: 1px solid #d5dbe0;
    border-radius: 5px;

    outline: none;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #dceefa;

    color: #202124;
}

QListWidget::item:hover {
    background-color: #eef6fb;
}


/* ==================================================================
   PLAIN TEXT DISPLAY
   ================================================================== */

QPlainTextEdit {
    background-color: #ffffff;

    color: #282d31;

    border: 1px solid #d5dbe0;
    border-radius: 5px;

    padding: 6px;

    selection-background-color: #dceefa;
}


/* ==================================================================
   PROGRESS BAR
   ================================================================== */

QProgressBar {
    background-color: #e7ebee;

    border: 1px solid #d2d7db;
    border-radius: 6px;

    min-height: 12px;

    max-height: 12px;
}

QProgressBar::chunk {
    background-color: #4b9bd3;

    border-radius: 5px;
}


/* ==================================================================
   SCROLL AREA
   ================================================================== */

QScrollArea {
    background-color: #f4f6f8;

    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #f4f6f8;
}


/* ==================================================================
   VERTICAL SCROLLBAR
   ================================================================== */

QScrollBar:vertical {
    background-color: #f0f2f4;

    width: 12px;

    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #bcc4ca;

    border-radius: 5px;

    min-height: 28px;

    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9fa9b0;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}


/* ==================================================================
   HORIZONTAL SCROLLBAR
   ================================================================== */

QScrollBar:horizontal {
    background-color: #f0f2f4;

    height: 12px;

    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #bcc4ca;

    border-radius: 5px;

    min-width: 28px;

    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #9fa9b0;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}


/* ==================================================================
   TOOLTIPS
   ================================================================== */

QToolTip {
    background-color: #ffffff;

    color: #202124;

    border: 1px solid #adb5bd;

    padding: 5px;
}

"""


# ------------------------------------------------------------------
# SECTION 2: RETURN APPLICATION STYLESHEET
# ------------------------------------------------------------------
def get_application_style():
    return APP_STYLE


# ------------------------------------------------------------------
# SECTION 3: APPLY APPLICATION STYLESHEET
# ------------------------------------------------------------------
def apply_app_style(application):
    application.setStyleSheet(APP_STYLE)