"""
Module: oracle_identifier_validator.py

Purpose:
Validates Oracle schema, table, and column identifiers before they are
used in dynamically constructed SQL statements.

Main responsibilities:
- Validate normal unquoted Oracle identifiers.
- Reject identifiers containing spaces, punctuation, SQL fragments,
  or other unsafe characters.
- Enforce the maximum identifier length supported by the framework.
- Provide reusable identifier-validation functions for configuration
  validation and database-access modules.
- Raise clear validation errors when invalid identifiers are supplied.

The framework intentionally supports normal unquoted Oracle identifiers
only. Quoted identifiers such as "Customer Table" are not supported.

This module does not access Oracle, execute SQL, or perform anonymization.
"""

import re


# ------------------------------------------------------------------
# SECTION 1: DEFINE ORACLE IDENTIFIER RULE
# ------------------------------------------------------------------
# DataAnonFramework deliberately supports normal unquoted Oracle names.
#
# Valid examples:
# DA_CUSTOMER
# CUSTOMER_2026
# BOT$TEMP
# BOT#DATA
#
# Invalid examples:
# DA-CUSTOMER
# DA CUSTOMER
# 123CUSTOMER
# CUSTOMER;DROP
#
# The first character must be alphabetic.
# Remaining characters may contain:
# A-Z, a-z, 0-9, _, $, #
ORACLE_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_$#]*$"
)

# Oracle modern identifiers normally support up to 128 bytes.
# DataAnonFramework uses ASCII-style unquoted identifiers, therefore
# character length and byte length are effectively the same here.
MAX_IDENTIFIER_LENGTH = 128


def validate_oracle_identifier(identifier, identifier_type="identifier"):
    # ------------------------------------------------------------------
    # SECTION 2: VALIDATE IDENTIFIER PRESENCE
    # ------------------------------------------------------------------
    # An identifier must be supplied before any other validation occurs.
    if identifier is None:
        raise ValueError(
            f"Oracle {identifier_type} is required."
        )

    # Convert to string and remove accidental leading/trailing whitespace.
    identifier = str(identifier).strip()

    if not identifier:
        raise ValueError(
            f"Oracle {identifier_type} is required."
        )

    # ------------------------------------------------------------------
    # SECTION 3: VALIDATE IDENTIFIER LENGTH
    # ------------------------------------------------------------------
    if len(identifier) > MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"Oracle {identifier_type} '{identifier}' exceeds "
            f"{MAX_IDENTIFIER_LENGTH} characters."
        )

    # ------------------------------------------------------------------
    # SECTION 4: VALIDATE IDENTIFIER CHARACTERS
    # ------------------------------------------------------------------
    # Reject anything that does not match the restricted Oracle
    # unquoted-identifier format used by DataAnonFramework.
    if not ORACLE_IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(
            f"Invalid Oracle {identifier_type}: '{identifier}'. "
            f"Use letters, numbers, _, $ or #, and begin with a letter."
        )

    # ------------------------------------------------------------------
    # SECTION 5: RETURN NORMALIZED IDENTIFIER
    # ------------------------------------------------------------------
    # Oracle stores normal unquoted identifiers in uppercase.
    #
    # Returning uppercase also makes identifier handling consistent
    # throughout DataAnonFramework.
    return identifier.upper()


def is_valid_oracle_identifier(identifier):
    # ------------------------------------------------------------------
    # SECTION 6: BOOLEAN IDENTIFIER CHECK
    # ------------------------------------------------------------------
    # This helper is useful when the calling module needs True/False
    # instead of a raised ValueError.
    try:
        validate_oracle_identifier(identifier)
        return True

    except ValueError:
        return False