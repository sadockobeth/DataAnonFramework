"""
Module: oracle_connection.py

Purpose:
Creates Oracle database connections for both the CLI and GUI versions
of DataAnonFramework.

Main responsibilities:
- Load the predefined CLI database connection settings from the .env file.
- Create an Oracle connection using .env settings when called by the CLI.
- Create an Oracle connection using connection information supplied dynamically by the GUI.
- Allow the CLI and GUI to share the same database connection module.
- Record successful and failed database connection attempts in the technical log.
- Prevent database passwords and connection credentials from being written to log files.

CLI connection failures are displayed and return None, while GUI connection
errors are logged and allowed to return to the GUI so they can be displayed
to the user.

This module does not store database credentials permanently and does not
perform metadata discovery, anonymization, or data processing.
"""

import os

import oracledb
from dotenv import load_dotenv

from app_logging.log_manager import get_logger


# ------------------------------------------------------------------
# SECTION 1: LOAD CLI ENVIRONMENT CONFIGURATION
# ------------------------------------------------------------------
# Load database connection information from the project's .env file.
# This configuration is used only when connect_to_oracle() is called
# without a GUI connection configuration.
load_dotenv()


# ------------------------------------------------------------------
# SECTION 2: CREATE APPLICATION LOGGER
# ------------------------------------------------------------------
# Use the shared DataAnonFramework technical logger.
#
# Database passwords and complete connection configurations are never
# written to this logger.
logger = get_logger()


def connect_to_oracle(connection_config=None):
    # ------------------------------------------------------------------
    # SECTION 3: HANDLE CLI DATABASE CONNECTION
    # ------------------------------------------------------------------
    # When no connection configuration is supplied, the request comes
    # from the CLI and database settings are read from .env.
    if connection_config is None:
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        hostname = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "1521")
        service_name = os.getenv("DB_SERVICE")

        # ------------------------------------------------------------------
        # SECTION 4: VALIDATE CLI CONFIGURATION
        # ------------------------------------------------------------------
        # Required .env values must be available before attempting Oracle
        # connectivity.
        if not username or not password or not hostname or not service_name:
            logger.error(
                "CLI Oracle connection failed because database configuration is incomplete."
            )

            print("Database configuration is incomplete.")
            print("Check the .env file.")

            return None

        # Construct the Oracle Easy Connect DSN.
        dsn = f"{hostname}:{port}/{service_name}"

        try:
            # ------------------------------------------------------------------
            # SECTION 5: CREATE CLI ORACLE CONNECTION
            # ------------------------------------------------------------------
            connection = oracledb.connect(
                user=username,
                password=password,
                dsn=dsn
            )

            # Log only the result of the operation.
            # Do not log the username, password, or complete DSN.
            logger.info("CLI Oracle connection successful.")

            print("Connection successful.")

            return connection

        except oracledb.Error as error:
            # ------------------------------------------------------------------
            # SECTION 6: HANDLE CLI CONNECTION FAILURE
            # ------------------------------------------------------------------
            # exception() records the Oracle error and traceback.
            #
            # The connection credentials themselves are not logged.
            logger.exception(
                "CLI Oracle connection failed: %s",
                error
            )

            print("Connection failed.")
            print(error)

            return None

    # ------------------------------------------------------------------
    # SECTION 7: READ GUI DATABASE CONFIGURATION
    # ------------------------------------------------------------------
    # GUI connection information is supplied dynamically by
    # DatabaseConnectionPanel.
    username = connection_config["username"]
    password = connection_config["password"]
    hostname = connection_config["host"]
    port = connection_config["port"]
    service_name = connection_config["service_name"]

    # Build the Oracle Easy Connect DSN in memory only.
    dsn = f"{hostname}:{port}/{service_name}"

    try:
        # ------------------------------------------------------------------
        # SECTION 8: CREATE GUI ORACLE CONNECTION
        # ------------------------------------------------------------------
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )

        # Do not include credentials or DSN in the technical log.
        logger.info("GUI Oracle connection successful.")

        return connection

    except oracledb.Error as error:
        # ------------------------------------------------------------------
        # SECTION 9: HANDLE GUI CONNECTION FAILURE
        # ------------------------------------------------------------------
        # Record the Oracle error for troubleshooting.
        #
        # Unlike CLI mode, the exception is re-raised so the GUI component
        # that requested the connection can display the error to the user.
        logger.exception(
            "GUI Oracle connection failed: %s",
            error
        )

        raise