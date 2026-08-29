"""
Module: database_connection_panel.py

Purpose:
Provides the Oracle database connection controls used by the GUI.

Main responsibilities:
- Accept Oracle host, port, service name, username, and password.
- Keep database credentials only in application memory.
- Validate required connection information.
- Test the Oracle database connection.
- Store connection configuration only after a successful test.
- Notify other GUI components when a tested connection is available.
- Invalidate a previously tested connection when connection fields change.
- Clear connection information when starting a new application session.
- Record connection test activity without logging credentials.

This module does not save database passwords, retrieve table metadata,
perform anonymization, or execute data-processing operations.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel
)

from database.oracle_connection import connect_to_oracle
from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
logger = get_logger()


class DatabaseConnectionPanel(QWidget):

    # ------------------------------------------------------------------
    # SIGNAL: TESTED DATABASE CONNECTION AVAILABLE
    # ------------------------------------------------------------------
    # The signal sends a successfully tested in-memory connection
    # configuration to other GUI components.
    connection_ready = Signal(object)

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # SECTION 2: CREATE DATABASE CONNECTION INPUTS
        # ------------------------------------------------------------------
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.service_name_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        # Oracle's standard listener port is used as the initial value.
        self.port_input.setText("1521")

        # Password must never be displayed as plain text in the GUI.
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        # Helpful examples are displayed only when fields are empty.
        self.host_input.setPlaceholderText(
            "Database host"
        )

        self.port_input.setPlaceholderText(
            "1521"
        )

        self.service_name_input.setPlaceholderText(
            "Service name"
        )

        self.username_input.setPlaceholderText(
            "Username"
        )

        self.password_input.setPlaceholderText(
            "Password"
        )

        # Port does not need the same width as the other fields.
        self.port_input.setMaximumWidth(
            90
        )

        # ------------------------------------------------------------------
        # SECTION 3: CREATE TEST CONNECTION BUTTON
        # ------------------------------------------------------------------
        self.test_connection_button = QPushButton(
            "Test Connection"
        )

        # Use the primary blue-button style defined in app_style.py.
        self.test_connection_button.setObjectName(
            "primaryButton"
        )

        # ------------------------------------------------------------------
        # SECTION 4: CREATE STATUS LABEL
        # ------------------------------------------------------------------
        self.status_label = QLabel(
            "Enter database connection details and test the connection."
        )

        # ------------------------------------------------------------------
        # SECTION 5: STORE TESTED CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # Database credentials exist only in application memory.
        #
        # A connection configuration is stored here only after the database
        # connection has been successfully tested.
        self.connection_config = None

        # ------------------------------------------------------------------
        # SECTION 6: CREATE COMPACT HORIZONTAL CONNECTION LAYOUT
        # ------------------------------------------------------------------
        # Labels are placed above the corresponding fields. This produces
        # the compact horizontal layout used in the approved GUI design.
        connection_grid = QGridLayout()

        connection_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        connection_grid.setHorizontalSpacing(
            10
        )

        connection_grid.setVerticalSpacing(
            4
        )

        # --------------------------------------------------------------
        # FIELD LABELS
        # --------------------------------------------------------------
        connection_grid.addWidget(
            QLabel("Host"),
            0,
            0
        )

        connection_grid.addWidget(
            QLabel("Port"),
            0,
            1
        )

        connection_grid.addWidget(
            QLabel("Service Name"),
            0,
            2
        )

        connection_grid.addWidget(
            QLabel("Username"),
            0,
            3
        )

        connection_grid.addWidget(
            QLabel("Password"),
            0,
            4
        )

        # --------------------------------------------------------------
        # FIELD INPUTS
        # --------------------------------------------------------------
        connection_grid.addWidget(
            self.host_input,
            1,
            0
        )

        connection_grid.addWidget(
            self.port_input,
            1,
            1
        )

        connection_grid.addWidget(
            self.service_name_input,
            1,
            2
        )

        connection_grid.addWidget(
            self.username_input,
            1,
            3
        )

        connection_grid.addWidget(
            self.password_input,
            1,
            4
        )

        # Give the larger connection fields more available width.
        connection_grid.setColumnStretch(
            0,
            2
        )

        connection_grid.setColumnStretch(
            1,
            0
        )

        connection_grid.setColumnStretch(
            2,
            2
        )

        connection_grid.setColumnStretch(
            3,
            1
        )

        connection_grid.setColumnStretch(
            4,
            1
        )

        # ------------------------------------------------------------------
        # SECTION 7: CREATE ACTION ROW
        # ------------------------------------------------------------------
        # Place the connection status on the left and the main action on
        # the right, similar to the approved mockup.
        action_layout = QHBoxLayout()

        action_layout.setContentsMargins(
            0,
            4,
            0,
            0
        )

        action_layout.addWidget(
            self.status_label
        )

        action_layout.addStretch()

        action_layout.addWidget(
            self.test_connection_button
        )

        # ------------------------------------------------------------------
        # SECTION 8: CREATE PANEL LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()

        # MainWindow's QGroupBox already supplies outer section spacing,
        # therefore keep the panel's internal margins small.
        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            5
        )

        layout.addLayout(
            connection_grid
        )

        layout.addLayout(
            action_layout
        )

        self.setLayout(
            layout
        )

        # ------------------------------------------------------------------
        # SECTION 9: CONNECT GUI EVENTS
        # ------------------------------------------------------------------
        self.test_connection_button.clicked.connect(
            self.test_connection
        )

        # Any modification to the connection fields invalidates a previously
        # tested connection. The user must test the new configuration before
        # it can be used by the remaining GUI workflow.
        self.host_input.textChanged.connect(
            self.invalidate_connection
        )

        self.port_input.textChanged.connect(
            self.invalidate_connection
        )

        self.service_name_input.textChanged.connect(
            self.invalidate_connection
        )

        self.username_input.textChanged.connect(
            self.invalidate_connection
        )

        self.password_input.textChanged.connect(
            self.invalidate_connection
        )

    def invalidate_connection(self):
        # ------------------------------------------------------------------
        # SECTION 10: INVALIDATE PREVIOUSLY TESTED CONNECTION
        # ------------------------------------------------------------------
        # If connection information changes after a successful test, the
        # previous configuration must no longer be considered valid.
        if self.connection_config is not None:
            self.connection_config = None

            self.status_label.setStyleSheet("")

            self.status_label.setText(
                "Connection details changed. Test the connection again."
            )

    def build_connection_config(self):
        # ------------------------------------------------------------------
        # SECTION 11: BUILD IN-MEMORY CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # Read values directly from the GUI.
        #
        # Password is retained only in memory and is never written to disk
        # by this panel.
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        service_name = self.service_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # ------------------------------------------------------------------
        # SECTION 12: VALIDATE REQUIRED CONNECTION INFORMATION
        # ------------------------------------------------------------------
        if not host:
            raise ValueError(
                "Enter database host."
            )

        if not port_text:
            raise ValueError(
                "Enter database port."
            )

        try:
            port = int(
                port_text
            )

        except ValueError:
            raise ValueError(
                "Database port must be a number."
            )

        if port < 1 or port > 65535:
            raise ValueError(
                "Database port must be between 1 and 65535."
            )

        if not service_name:
            raise ValueError(
                "Enter Oracle service name."
            )

        if not username:
            raise ValueError(
                "Enter database username."
            )

        if not password:
            raise ValueError(
                "Enter database password."
            )

        return {
            "host": host,
            "port": port,
            "service_name": service_name,
            "username": username,
            "password": password
        }

    def test_connection(self):
        # ------------------------------------------------------------------
        # SECTION 13: PREPARE DATABASE CONNECTION TEST
        # ------------------------------------------------------------------
        # Never retain an old tested configuration while testing different
        # connection information.
        self.connection_config = None

        connection = None

        try:
            connection_config = self.build_connection_config()

            self.status_label.setStyleSheet("")

            self.status_label.setText(
                "Testing database connection..."
            )

            # ------------------------------------------------------------------
            # SECTION 14: TEST ORACLE CONNECTION
            # ------------------------------------------------------------------
            connection = connect_to_oracle(
                connection_config
            )

            # ------------------------------------------------------------------
            # SECTION 15: STORE SUCCESSFULLY TESTED CONFIGURATION
            # ------------------------------------------------------------------
            # Keep the configuration only in memory.
            self.connection_config = connection_config

            self.status_label.setStyleSheet(
                "color: green; font-weight: bold;"
            )

            self.status_label.setText(
                "✓ Connection successful."
            )

            logger.info(
                "GUI Oracle database connection test successful."
            )

            # Notify SourceTablePanel and any future interested GUI component
            # that a tested connection is now available.
            self.connection_ready.emit(
                self.connection_config
            )

        except ValueError as error:
            # ------------------------------------------------------------------
            # SECTION 16: HANDLE INPUT VALIDATION FAILURE
            # ------------------------------------------------------------------
            self.connection_config = None

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                f"Connection not tested: {error}"
            )

            logger.warning(
                "GUI Oracle connection test stopped because connection "
                "information was incomplete or invalid."
            )

        except Exception:
            # ------------------------------------------------------------------
            # SECTION 17: HANDLE DATABASE CONNECTION FAILURE
            # ------------------------------------------------------------------
            # Do not place credentials, host, service name, DSN, or the
            # complete connection configuration in the technical log.
            self.connection_config = None

            self.status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.status_label.setText(
                "Connection failed. Verify the database connection details."
            )

            logger.exception(
                "GUI Oracle database connection test failed."
            )

        finally:
            # ------------------------------------------------------------------
            # SECTION 18: CLOSE TEST CONNECTION
            # ------------------------------------------------------------------
            # The connection is required only to verify connectivity.
            if connection is not None:
                connection.close()

    def get_connection_config(self):
        # ------------------------------------------------------------------
        # SECTION 19: RETURN TESTED CONNECTION CONFIGURATION
        # ------------------------------------------------------------------
        # None means the current GUI connection information has not been
        # successfully tested.
        return self.connection_config

    def clear_panel(self):
        # ------------------------------------------------------------------
        # SECTION 20: CLEAR DATABASE CONNECTION PANEL
        # ------------------------------------------------------------------
        # Clear credentials and any previously tested in-memory configuration.
        self.connection_config = None

        self.host_input.clear()
        self.service_name_input.clear()
        self.username_input.clear()
        self.password_input.clear()

        # Restore the standard Oracle listener port.
        self.port_input.setText(
            "1521"
        )

        self.status_label.setStyleSheet("")

        self.status_label.setText(
            "Enter database connection details and test the connection."
        )