"""
Module: database_connection_panel.py

Purpose:
Collects and validates Oracle database connection information from the GUI user.

Main responsibilities:
- Accept Oracle host, port, service name, username, and password.
- Hide the password while it is being entered.
- Validate required connection information.
- Test the Oracle database connection.
- Keep the successfully tested connection configuration in memory.
- Notify other GUI components when a valid connection is available.
- Invalidate the active connection configuration if the user changes its details.
- Clear connection information when starting a new session.

This module does not store database credentials permanently, retrieve
table data, or perform anonymization.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel

from database.oracle_connection import connect_to_oracle
from gui.status_helper import set_status


class DatabaseConnectionPanel(QWidget):

    # ------------------------------------------------------------------
    # SIGNAL: DATABASE CONNECTION READY
    # ------------------------------------------------------------------
    # This signal announces that the entered Oracle connection details
    # have been tested successfully.
    connection_ready = Signal(object)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 1: INITIALIZE CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # None means there is currently no successfully tested GUI connection.
        self.connection_config = None

        # ------------------------------------------------------------------
        # SECTION 2: CREATE CONNECTION INPUT FIELDS
        # ------------------------------------------------------------------
        # QLineEdit provides text boxes for Oracle connection information.
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.service_name_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        # Oracle commonly uses listener port 1521, so provide it by default.
        self.port_input.setText("1521")

        # Password mode hides the characters entered by the user.
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # ------------------------------------------------------------------
        # SECTION 3: CREATE TEST CONNECTION BUTTON
        # ------------------------------------------------------------------
        # The supplied configuration becomes active only after a successful test.
        self.test_connection_button = QPushButton("Test Connection")

        # ------------------------------------------------------------------
        # SECTION 4: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        # QLabel displays connection validation and test results.
        self.status_label = QLabel("Status: Connection not configured")

        # ------------------------------------------------------------------
        # SECTION 5: CREATE CONNECTION FORM
        # ------------------------------------------------------------------
        # QFormLayout places each label beside its corresponding input field.
        form_layout = QFormLayout()
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Service Name:", self.service_name_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)

        # ------------------------------------------------------------------
        # SECTION 6: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        # QVBoxLayout arranges the form, button, and status vertically.
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.test_connection_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # ------------------------------------------------------------------
        # SECTION 7: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        # Test the supplied connection when the button is clicked.
        self.test_connection_button.clicked.connect(self.test_connection)

        # If connection details are changed after a successful test,
        # require the user to test the new configuration again.
        self.host_input.textChanged.connect(self.invalidate_connection)
        self.port_input.textChanged.connect(self.invalidate_connection)
        self.service_name_input.textChanged.connect(self.invalidate_connection)
        self.username_input.textChanged.connect(self.invalidate_connection)
        self.password_input.textChanged.connect(self.invalidate_connection)

    def get_entered_config(self):
        # ------------------------------------------------------------------
        # SECTION 8: READ CONNECTION INFORMATION
        # ------------------------------------------------------------------
        # Read the values currently entered in the GUI.
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        service_name = self.service_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # ------------------------------------------------------------------
        # SECTION 9: VALIDATE REQUIRED FIELDS
        # ------------------------------------------------------------------
        if not host or not port or not service_name or not username or not password:
            set_status(self.status_label, "Status: Complete all connection fields.", error=True)
            return None

        if not port.isdigit():
            set_status(self.status_label, "Status: Port must be a number.", error=True)
            return None

        # ------------------------------------------------------------------
        # SECTION 10: BUILD CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # The password remains only in application memory.
        return {
            "host": host,
            "port": int(port),
            "service_name": service_name,
            "username": username,
            "password": password
        }

    def test_connection(self):
        # ------------------------------------------------------------------
        # SECTION 11: TEST ORACLE CONNECTION
        # ------------------------------------------------------------------
        connection_config = self.get_entered_config()

        if connection_config is None:
            return

        connection = None

        try:
            self.status_label.setText("Status: Connecting...")

            # Passing connection_config tells oracle_connection.py
            # to use GUI values instead of CLI .env values.
            connection = connect_to_oracle(connection_config)

            # Store only successfully tested connection information.
            self.connection_config = connection_config
            self.status_label.setStyleSheet("font-weight: bold;")
            self.status_label.setText("Status: Database connection successful.")

            # ------------------------------------------------------------------
            # SECTION 12: NOTIFY OTHER GUI COMPONENTS
            # ------------------------------------------------------------------
            # Broadcast the validated connection configuration.
            self.connection_ready.emit(self.connection_config)

        except Exception as error:
            self.connection_config = None
            set_status(self.status_label, f"Status: Connection failed - {error}", error=True)

        finally:
            if connection is not None:
                connection.close()

    def invalidate_connection(self):
        # ------------------------------------------------------------------
        # SECTION 13: INVALIDATE CHANGED CONNECTION
        # ------------------------------------------------------------------
        # A configuration that has changed after testing must be tested again.
        if self.connection_config is not None:
            self.connection_config = None
            set_status(self.status_label, "Status: Connection details changed. Test connection again.", error=True)

    def get_connection_config(self):
        # ------------------------------------------------------------------
        # SECTION 14: RETURN ACTIVE CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # Only successfully tested connection information is returned.
        return self.connection_config

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 15: CLEAR CONNECTION PANEL
        # ------------------------------------------------------------------
        # Remove all current connection information when starting afresh.
        self.host_input.clear()
        self.port_input.setText("1521")
        self.service_name_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.connection_config = None
        set_status(self.status_label, "Status: Connection not configured", error=True)