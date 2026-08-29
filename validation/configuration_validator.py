"""
Module: configuration_validator.py

Purpose:
Validates DataAnonFramework configuration before preview or execution.

Main responsibilities:
- Validate source schema and source table configuration.
- Validate that source metadata has been loaded.
- Validate that anonymization rules have been selected.
- Validate that every rule references an existing source column.
- Validate anonymization strategies against Oracle column datatypes.
- Validate target schema and target table configuration.
- Detect conflicts between anonymized and excluded columns.
- Validate excluded columns against loaded source metadata.
- Prevent all source columns from being excluded.
- Provide the same validation logic for both GUI preview and execution.

This module does not access Oracle, transform data, create target tables,
or write data.
"""

from validation.strategy_validator import is_strategy_allowed


def validate_configuration(source_config, rules, target_config):

    # ------------------------------------------------------------------
    # SECTION 1: VALIDATE SOURCE CONFIGURATION
    # ------------------------------------------------------------------
    # Source schema and source table are required.
    if not source_config["source_schema"]:
        return "Source schema is required."

    if not source_config["source_table"]:
        return "Source table is required."

    # Source metadata must already have been loaded from Oracle.
    if not source_config["table_columns"]:
        return "Load the source table columns first."

    # ------------------------------------------------------------------
    # SECTION 2: BUILD SOURCE COLUMN METADATA LOOKUP
    # ------------------------------------------------------------------
    # Create a dictionary that allows fast lookup of the Oracle datatype
    # for each loaded source column.
    #
    # Example:
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
    # SECTION 3: VALIDATE ANONYMIZATION RULES
    # ------------------------------------------------------------------
    # At least one anonymization rule must be configured.
    if not rules:
        return "At least one anonymization rule is required."

    # ------------------------------------------------------------------
    # SECTION 4: VALIDATE RULE COLUMNS AND DATATYPES
    # ------------------------------------------------------------------
    # Every anonymization rule must reference an existing source column,
    # and its strategy must be compatible with the Oracle datatype.
    for column_name, strategy in rules.items():

        if column_name not in column_types:
            return f"Rule references unknown source column: {column_name}"

        data_type = column_types[column_name]

        if not is_strategy_allowed(data_type, strategy):
            return f"{strategy} is not compatible with {column_name} ({data_type})."

    # ------------------------------------------------------------------
    # SECTION 5: VALIDATE TARGET CONFIGURATION
    # ------------------------------------------------------------------
    # OUT_PLACE anonymization requires both a target schema and table.
    if not target_config["target_schema"]:
        return "Target schema is required."

    if not target_config["target_table"]:
        return "Target table is required."

    # ------------------------------------------------------------------
    # SECTION 6: VALIDATE EXCLUDED COLUMNS
    # ------------------------------------------------------------------
    # Every excluded column must belong to the loaded source table.
    excluded_columns = target_config["excluded_columns"]

    for column_name in excluded_columns:
        if column_name not in source_columns:
            return f"Excluded column does not exist in the source table: {column_name}"

    # ------------------------------------------------------------------
    # SECTION 7: VALIDATE RULE AND EXCLUSION CONFLICTS
    # ------------------------------------------------------------------
    # A column cannot simultaneously have an anonymization rule and also
    # be removed completely from the OUT_PLACE target table.
    conflicting_columns = [column for column in rules if column in excluded_columns]

    if conflicting_columns:
        return f"Column cannot be anonymized and excluded: {', '.join(conflicting_columns)}"

    # ------------------------------------------------------------------
    # SECTION 8: PREVENT EXCLUDING ALL SOURCE COLUMNS
    # ------------------------------------------------------------------
    # At least one source column must remain in the target table.
    if len(excluded_columns) == len(source_columns):
        return "All source columns cannot be excluded."

    # ------------------------------------------------------------------
    # SECTION 9: VALIDATION SUCCESSFUL
    # ------------------------------------------------------------------
    # None means no configuration problem was detected.
    return None