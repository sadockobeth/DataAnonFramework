"""
Module: status_helper.py

Purpose:
Provides consistent status-message formatting across the GUI.

Main responsibilities:
- Display normal informational messages.
- Display error messages in red for better visibility.
- Reset the label style when switching from an error to a normal message.

This module does not contain application or database logic.
"""


def set_status(label, message, error=False):
    # ------------------------------------------------------------------
    # SECTION 1: SET STATUS MESSAGE
    # ------------------------------------------------------------------
    # Error messages are displayed in red while normal status messages
    # use the application's default text color.
    if error:
        label.setStyleSheet("color: red;")
    else:
        label.setStyleSheet("")

    label.setText(message)