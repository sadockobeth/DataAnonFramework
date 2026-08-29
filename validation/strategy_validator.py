"""
Module: strategy_validator.py

Purpose:
Defines which anonymization strategies are compatible with Oracle datatypes.

Main responsibilities:
- Identify anonymization strategies supported by each Oracle datatype.
- Prevent strategies that would produce values incompatible with the
  original target column datatype.
- Provide shared datatype-validation logic that can be reused by both
  GUI and CLI components.

This module does not perform anonymization or access the database.
"""


def get_allowed_strategies(data_type):
    # ------------------------------------------------------------------
    # SECTION 1: NORMALIZE ORACLE DATATYPE
    # ------------------------------------------------------------------
    # Convert the datatype to uppercase so comparisons are consistent.
    data_type = data_type.upper().strip()

    # ------------------------------------------------------------------
    # SECTION 2: CHARACTER DATATYPES
    # ------------------------------------------------------------------
    # MASKING and TOKENIZATION both return character values and are
    # therefore appropriate for character-based Oracle columns.
    character_types = {"VARCHAR2", "VARCHAR", "CHAR", "NVARCHAR2", "NCHAR", "CLOB", "NCLOB"}

    if data_type in character_types:
        return ["MASKING", "TOKENIZATION"]

    # ------------------------------------------------------------------
    # SECTION 3: NUMERIC DATATYPES
    # ------------------------------------------------------------------
    # GENERALIZATION and PERTURBATION preserve numeric output.
    numeric_types = {"NUMBER", "FLOAT", "BINARY_FLOAT", "BINARY_DOUBLE", "INTEGER", "DECIMAL"}

    if data_type in numeric_types:
        return ["GENERALIZATION", "PERTURBATION"]

    # ------------------------------------------------------------------
    # SECTION 4: DATE AND TIMESTAMP DATATYPES
    # ------------------------------------------------------------------
    # DATE_SHIFT returns another date/datetime value.
    if data_type == "DATE" or data_type.startswith("TIMESTAMP"):
        return ["DATE_SHIFT"]

    # ------------------------------------------------------------------
    # SECTION 5: UNSUPPORTED DATATYPES
    # ------------------------------------------------------------------
    # An empty list means DataAnonFramework currently has no compatible
    # anonymization method for this datatype.
    return []


def is_strategy_allowed(data_type, strategy):
    # ------------------------------------------------------------------
    # SECTION 6: VALIDATE STRATEGY AGAINST DATATYPE
    # ------------------------------------------------------------------
    # Return True only when the requested strategy appears in the list
    # of strategies supported by the Oracle datatype.
    return strategy in get_allowed_strategies(data_type)