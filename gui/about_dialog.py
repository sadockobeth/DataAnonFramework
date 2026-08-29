"""
Module: about_dialog.py

Purpose:
Displays information about the Data Anonymization Engine in a dedicated
About dialog.

Main responsibilities:
- Display the company logo.
- Display the application name and version.
- Display a simple description of the application.
- Present the main capabilities using language suitable for all users.
- Provide a clean and reusable About window.

This module does not access Oracle, perform anonymization, or manage
application execution.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton
)

from app_info import APP_NAME, APP_VERSION, APP_DESCRIPTION


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        # ------------------------------------------------------------------
        # SECTION 1: CONFIGURE ABOUT WINDOW
        # ------------------------------------------------------------------
        self.setWindowTitle(f"About {APP_NAME}")

        # Keep the About window compact and easy to read.
        self.setMinimumWidth(500)

        # ------------------------------------------------------------------
        # SECTION 2: CREATE MAIN LAYOUT
        # ------------------------------------------------------------------
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ------------------------------------------------------------------
        # SECTION 3: DISPLAY COMPANY LOGO
        # ------------------------------------------------------------------
        # Locate the logo relative to the project root.
        project_root = Path(__file__).resolve().parent.parent
        logo_path = project_root / "assets" / "bot_logo.png"

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))

            # Scale the logo while preserving its original proportions.
            logo_pixmap = logo_pixmap.scaled(
                180,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.logo_label.setPixmap(logo_pixmap)

        else:
            # The dialog should still work even when the logo file
            # cannot be found.
            self.logo_label.setText("Company Logo")
            self.logo_label.setStyleSheet(
                "font-weight: bold;"
            )

        layout.addWidget(self.logo_label)

        # ------------------------------------------------------------------
        # SECTION 4: DISPLAY APPLICATION NAME
        # ------------------------------------------------------------------
        self.name_label = QLabel(
            f"<h2>{APP_NAME}</h2>"
        )

        self.name_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(self.name_label)

        # ------------------------------------------------------------------
        # SECTION 5: DISPLAY APPLICATION VERSION
        # ------------------------------------------------------------------
        self.version_label = QLabel(
            f"Version {APP_VERSION}"
        )

        self.version_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(self.version_label)

        # ------------------------------------------------------------------
        # SECTION 6: DISPLAY APPLICATION DESCRIPTION
        # ------------------------------------------------------------------
        self.description_label = QLabel(
            APP_DESCRIPTION
        )

        self.description_label.setWordWrap(
            True
        )

        self.description_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(self.description_label)

        # ------------------------------------------------------------------
        # SECTION 7: DISPLAY MAIN CAPABILITIES
        # ------------------------------------------------------------------
        # Present the main capabilities using simple language that can be
        # understood by both technical and non-technical users.
        capabilities_text = (
            "<b>Main Capabilities</b><br><br>"

            "• <b>Select data to be protected</b> - "
            "Allows users to choose the database table and information "
            "that needs protection.<br><br>"

            "• <b>Identify and protect sensitive information</b> - "
            "Helps protect personal, confidential, and other sensitive data.<br><br>"

            "• <b>Apply different protection methods</b> - "
            "Provides different ways of changing sensitive information while "
            "keeping the data useful for its intended purpose.<br><br>"

            "• <b>Preview results before processing</b> - "
            "Allows users to review sample results before applying the changes "
            "to the complete dataset.<br><br>"

            "• <b>Keep the original data unchanged</b> - "
            "Creates a separate protected copy of the data without modifying "
            "the original source.<br><br>"

            "• <b>Process large amounts of data safely</b> - "
            "Supports controlled processing, safe cancellation, and protection "
            "against incomplete results.<br><br>"

            "• <b>Keep records of processing activities</b> - "
            "Provides execution summaries, history, and logs to help track "
            "what was processed and its outcome."
        )

        self.capabilities_label = QLabel(capabilities_text)
        self.capabilities_label.setWordWrap(True)

        layout.addWidget(self.capabilities_label)

        # ------------------------------------------------------------------
        # SECTION 8: CREATE CLOSE BUTTON
        # ------------------------------------------------------------------
        self.close_button = QPushButton(
            "Close"
        )

        self.close_button.clicked.connect(
            self.accept
        )

        layout.addWidget(self.close_button)

        # ------------------------------------------------------------------
        # SECTION 9: APPLY ABOUT WINDOW LAYOUT
        # ------------------------------------------------------------------
        self.setLayout(layout)