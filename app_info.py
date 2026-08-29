"""
Module: app_info.py

Purpose:
Provides centralized application identity and version information
for DataAnonFramework.

Main responsibilities:
- Define the official application name.
- Define the current application version.
- Define a short application description.
- Provide one shared source of application information for the GUI,
  technical logging, packaging, and future documentation.

This module does not create GUI components, access Oracle, or perform
anonymization.
"""


# ------------------------------------------------------------------
# SECTION 1: APPLICATION IDENTITY
# ------------------------------------------------------------------
# Keep application identity information in one location so version
# information is not duplicated across different modules.
APP_NAME = "Data Anonymization Engine"
APP_VERSION = "1.0.0"

APP_DESCRIPTION = (
    "Data Anonymization Engine for controlled, "
    "metadata-driven anonymization of sensitive data for"
    "testing, development, analysis, training, and other approved uses."
)