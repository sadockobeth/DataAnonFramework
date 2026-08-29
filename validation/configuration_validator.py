"""
Module: configuration_validator.py

Purpose:
Validates DataAnonFramework configuration before preview or execution.

Main responsibilities:
- Validate source schema and source table configuration.
- Validate Oracle schema and table identifiers before database operations.
- Validate that source metadata has been loaded.
- Validate that anonymization rules have been selected.
- Validate that every rule references an existing source column.
- Validate anonymization strategies against Oracle column datatypes.
- Validate target schema and target table configuration.
- Validate excluded columns against loaded source metadata.
- Detect conflicts between anonymized and excluded columns.
- Prevent all source columns from being excluded.
- Provide the same validation logic for GUI preview and execution.

This module does not access Oracle, transform data, create target tables,
or write data.
"""

from validation.strategy_validator import is_strategy_allowed
from validation.oracle_identifier_validator import validate_oracle_identifier


def validate_configuration(source_config, rules, target_config):
    # ------------------------------------------------------------------
    # SECTION 1: VALIDATE SOURCE CONFIGURATION
    # ------------------------------------------------------------------
    # Source schema and source table are required.
    if not source_config["source_schema"]:
        return "Source schema is required."

    if not source_config["source_table"]:
        return "Source table is required."

    # ------------------------------------------------------------------
    # SECTION 2: VALIDATE SOURCE ORACLE IDENTIFIERS
    # ------------------------------------------------------------------
    # Validate schema and table names before they are later used in
    # dynamically constructed Oracle SQL statements.
    try:
        validate_oracle_identifier(
            source_config["source_schema"],
            "source schema"
        )

        validate_oracle_identifier(
            source_config["source_table"],
            "source table"
        )

    except ValueError as error:
        return str(error)

    # ------------------------------------------------------------------
    # SECTION 3: VALIDATE SOURCE METADATA
    # ------------------------------------------------------------------
    # Source metadata must already have been loaded from Oracle.
    if not source_config["table_columns"]:
        return "Load the source table columns first."

    # ------------------------------------------------------------------
    # SECTION 4: BUILD SOURCE COLUMN METADATA LOOKUP
    # ------------------------------------------------------------------
    # Build a dictionary that allows quick datatype lookup.
    #
    # Example:
    #
    # {
    #     "FULL_NAME": "VARCHAR2",
    #     "DATE_OF_BIRTH": "DATE",
    #     "MONTHLY_INCOME": "NUMBER"
    # }
    column_types = {
        column["column_name"]: column["data_type"]
        for column in source_config["table_columns"]
    }

    source_columns = list(column_types.keys())

    # ------------------------------------------------------------------
    # SECTION 5: VALIDATE SOURCE COLUMN IDENTIFIERS
    # ------------------------------------------------------------------
    # Source column names come from Oracle metadata, but validating them
    # here provides another safety layer before dynamic SQL is generated.
    for column_name in source_columns:
        try:
            validate_oracle_identifier(
                column_name,
                "source column"
            )

        except ValueError as error:
            return str(error)

    # ------------------------------------------------------------------
    # SECTION 6: VALIDATE ANONYMIZATION RULES
    # ------------------------------------------------------------------
    # At least one anonymization rule must be configured.
    if not rules:
        return "At least one anonymization rule is required."

    # ------------------------------------------------------------------
    # SECTION 7: VALIDATE RULE COLUMNS AND DATATYPES
    # ------------------------------------------------------------------
    # Every anonymization rule must:
    #
    # 1. reference a valid Oracle column identifier,
    # 2. reference an existing source column,
    # 3. use a strategy compatible with the Oracle datatype.
    for column_name, strategy in rules.items():

        try:
            validate_oracle_identifier(
                column_name,
                "rule column"
            )

        except ValueError as error:
            return str(error)

        if column_name not in column_types:
            return f"Rule references unknown source column: {column_name}"

        data_type = column_types[column_name]

        if not is_strategy_allowed(
            data_type,
            strategy
        ):
            return (
                f"{strategy} is not compatible with "
                f"{column_name} ({data_type})."
            )

    # ------------------------------------------------------------------
    # SECTION 8: VALIDATE TARGET CONFIGURATION
    # ------------------------------------------------------------------
    # OUT_PLACE anonymization requires both a target schema and table.
    if not target_config["target_schema"]:
        return "Target schema is required."

    if not target_config["target_table"]:
        return "Target table is required."

    # ------------------------------------------------------------------
    # SECTION 9: VALIDATE TARGET ORACLE IDENTIFIERS
    # ------------------------------------------------------------------
    # Target schema and table names are supplied by the user and later
    # become part of dynamic CREATE TABLE and INSERT statements.
    try:
        validate_oracle_identifier(
            target_config["target_schema"],
            "target schema"
        )

        validate_oracle_identifier(
            target_config["target_table"],
            "target table"
        )

    except ValueError as error:
        return str(error)

    # ------------------------------------------------------------------
    # SECTION 10: VALIDATE EXCLUDED COLUMNS
    # ------------------------------------------------------------------
    # Every excluded column must:
    #
    # 1. be a valid Oracle identifier,
    # 2. exist in the loaded source table.
    excluded_columns = target_config["excluded_columns"]

    for column_name in excluded_columns:

        try:
            validate_oracle_identifier(
                column_name,
                "excluded column"
            )

        except ValueError as error:
            return str(error)

        if column_name not in source_columns:
            return (
                "Excluded column does not exist in the source table: "
                f"{column_name}"
            )

    # ------------------------------------------------------------------
    # SECTION 11: VALIDATE RULE AND EXCLUSION CONFLICTS
    # ------------------------------------------------------------------
    # A column cannot simultaneously have an anonymization rule and
    # also be removed completely from the OUT_PLACE target table.
    conflicting_columns = [
        column_name
        for column_name in rules
        if column_name in excluded_columns
    ]

    if conflicting_columns:
        return (
            "Column cannot be anonymized and excluded: "
            f"{', '.join(conflicting_columns)}"
        )

    # ------------------------------------------------------------------
    # SECTION 12: PREVENT EXCLUDING ALL SOURCE COLUMNS
    # ------------------------------------------------------------------
    # At least one source column must remain in the target table.
    if len(excluded_columns) == len(source_columns):
        return "All source columns cannot be excluded."

    # ------------------------------------------------------------------
    # SECTION 13: VALIDATION SUCCESSFUL
    # ------------------------------------------------------------------
    # None means no configuration problem was detected.
    return None