"""
Module: gui_main.py

Purpose:
Provides the entry point for starting the DataAnonFramework GUI.

Main responsibilities:
- Create the PySide6 QApplication object.
- Create the main DataAnonFramework window.
- Center the main window on the user's screen.
- Display the application window.
- Start the Qt event loop.
- Record GUI application startup and shutdown events in the technical log.

This module does not perform anonymization, access Oracle directly,
or contain GUI business logic.
"""

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from app_logging.log_manager import get_logger


def main():
    # ------------------------------------------------------------------
    # SECTION 1: CREATE APPLICATION LOGGER
    # ------------------------------------------------------------------
    # Retrieve the shared DataAnonFramework logger.
    #
    # The logger writes technical application events to:
    #
    # DataAnonFramework/logs/dataanonframework.log
    logger = get_logger()

    # Record application startup.
    logger.info("DataAnonFramework GUI started.")

    try:
        # ------------------------------------------------------------------
        # SECTION 2: CREATE QT APPLICATION
        # ------------------------------------------------------------------
        # QApplication manages the entire GUI application.
        app = QApplication(sys.argv)

        # ------------------------------------------------------------------
        # SECTION 3: CREATE MAIN WINDOW
        # ------------------------------------------------------------------
        # MainWindow creates and coordinates all GUI panels.
        window = MainWindow()

        # ------------------------------------------------------------------
        # SECTION 4: CENTER MAIN WINDOW
        # ------------------------------------------------------------------
        # availableGeometry() returns the usable desktop area.
        screen = app.primaryScreen().availableGeometry()

        # frameGeometry() returns the current window geometry.
        window_geometry = window.frameGeometry()

        # Move the center of the application window to the center
        # of the available desktop area.
        window_geometry.moveCenter(screen.center())

        # Move the actual window to the calculated position.
        window.move(window_geometry.topLeft())

        # ------------------------------------------------------------------
        # SECTION 5: DISPLAY MAIN WINDOW
        # ------------------------------------------------------------------
        # show() makes the DataAnonFramework GUI visible.
        window.show()

        # ------------------------------------------------------------------
        # SECTION 6: START QT EVENT LOOP
        # ------------------------------------------------------------------
        # app.exec() keeps the GUI running until the user closes it.
        exit_code = app.exec()

        # ------------------------------------------------------------------
        # SECTION 7: RECORD NORMAL APPLICATION SHUTDOWN
        # ------------------------------------------------------------------
        logger.info("DataAnonFramework GUI stopped.")

        return exit_code

    except Exception as error:
        # ------------------------------------------------------------------
        # SECTION 8: RECORD UNHANDLED STARTUP ERROR
        # ------------------------------------------------------------------
        # exception() records both the error message and Python traceback.
        logger.exception(
            "DataAnonFramework GUI terminated unexpectedly: %s",
            error
        )

        raise


# ----------------------------------------------------------------------
# PROGRAM ENTRY POINT
# ----------------------------------------------------------------------
# Python calls main() only when gui_main.py is executed directly.
if __name__ == "__main__":
    sys.exit(main())