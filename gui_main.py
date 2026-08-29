"""
Module: gui_main.py

Purpose:
Provides the entry point for starting the Data Aninymization Engine GUI.

Main responsibilities:
- Read centralized application identity and version information.
- Create the PySide6 QApplication object.
- Apply the shared application stylesheet.
- Create the main application window.
- Center the main window on the user's screen.
- Display the application window.
- Start the Qt event loop.
- Record GUI application startup and shutdown events in the technical log.

This module does not perform anonymization, access Oracle directly,
or contain GUI business logic.
"""

import sys

from PySide6.QtWidgets import QApplication

from app_info import APP_NAME, APP_VERSION
from gui.app_style import get_application_style
from gui.main_window import MainWindow
from app_logging.log_manager import get_logger


def main():
    # ------------------------------------------------------------------
    # SECTION 1: CREATE APPLICATION LOGGER
    # ------------------------------------------------------------------
    logger = get_logger()

    logger.info(
        "%s Version %s GUI started.",
        APP_NAME,
        APP_VERSION
    )

    try:
        # ------------------------------------------------------------------
        # SECTION 2: CREATE QT APPLICATION
        # ------------------------------------------------------------------
        # QApplication manages the complete GUI application.
        app = QApplication(sys.argv)

        # ------------------------------------------------------------------
        # SECTION 3: SET APPLICATION INFORMATION
        # ------------------------------------------------------------------
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)

        # ------------------------------------------------------------------
        # SECTION 4: APPLY SHARED GUI STYLE
        # ------------------------------------------------------------------
        # Styling is kept in app_style.py so presentation remains separate
        # from GUI behavior and business logic.
        app.setStyleSheet(
            get_application_style()
        )

        # ------------------------------------------------------------------
        # SECTION 5: CREATE MAIN WINDOW
        # ------------------------------------------------------------------
        window = MainWindow()

        # ------------------------------------------------------------------
        # SECTION 6: CENTER MAIN WINDOW
        # ------------------------------------------------------------------
        screen = app.primaryScreen().availableGeometry()
        window_geometry = window.frameGeometry()
        window_geometry.moveCenter(screen.center())
        window.move(window_geometry.topLeft())

        # ------------------------------------------------------------------
        # SECTION 7: DISPLAY MAIN WINDOW
        # ------------------------------------------------------------------
        window.show()

        # ------------------------------------------------------------------
        # SECTION 8: START QT EVENT LOOP
        # ------------------------------------------------------------------
        exit_code = app.exec()

        # ------------------------------------------------------------------
        # SECTION 9: RECORD NORMAL APPLICATION SHUTDOWN
        # ------------------------------------------------------------------
        logger.info(
            "%s Version %s GUI stopped.",
            APP_NAME,
            APP_VERSION
        )

        return exit_code

    except Exception as error:
        # ------------------------------------------------------------------
        # SECTION 10: RECORD UNHANDLED APPLICATION ERROR
        # ------------------------------------------------------------------
        logger.exception(
            "%s Version %s GUI terminated unexpectedly: %s",
            APP_NAME,
            APP_VERSION,
            error
        )

        raise


# ----------------------------------------------------------------------
# PROGRAM ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())