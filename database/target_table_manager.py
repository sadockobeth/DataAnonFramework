"""
Module: target_table_manager.py

Purpose:
Creates and removes OUT_PLACE Oracle target tables used by
DataAnonFramework.

Main responsibilities:
- Validate Oracle schema, table, and column identifiers before dynamic SQL.
- Determine which source columns should be included in the target table.
- Create an empty target table based on the source table structure.
- Exclude user-selected columns from the target table.
- Drop an existing target table when explicitly requested.
- Return the final list of columns included in the target table.

This module does not perform anonymization, insert transformed data,
commit DML transactions, or decide which columns are sensitive.

Oracle DDL statements such as CREATE TABLE and DROP TABLE implicitly
commit according to normal Oracle DDL behavior.
"""

from validation.oracle_identifier_validator import validate_oracle_identifier


def create_target_table(
    connection,
    source_schema,
    source_table,
    target_schema,
    target_table,
    source_columns,
    excluded_columns
):
    # ------------------------------------------------------------------
    # SECTION 1: VALIDATE SOURCE IDENTIFIERS
    # ------------------------------------------------------------------
    # Validate identifiers again at the database SQL boundary even though
    # configuration_validator.py normally validates them earlier.
    source_schema = validate_oracle_identifier(
        source_schema,
        "source schema"
    )

    source_table = validate_oracle_identifier(
        source_table,
        "source table"
    )

    # ------------------------------------------------------------------
    # SECTION 2: VALIDATE TARGET IDENTIFIERS
    # ------------------------------------------------------------------
    target_schema = validate_oracle_identifier(
        target_schema,
        "target schema"
    )

    target_table = validate_oracle_identifier(
        target_table,
        "target table"
    )

    # ------------------------------------------------------------------
    # SECTION 3: VALIDATE SOURCE COLUMN IDENTIFIERS
    # ------------------------------------------------------------------
    # Build a validated version of the source-column list before any
    # column names are included in dynamic SQL.
    validated_source_columns = []

    for column_name in source_columns:
        validated_column = validate_oracle_identifier(
            column_name,
            "source column"
        )

        validated_source_columns.append(
            validated_column
        )

    # ------------------------------------------------------------------
    # SECTION 4: VALIDATE EXCLUDED COLUMN IDENTIFIERS
    # ------------------------------------------------------------------
    validated_excluded_columns = []

    for column_name in excluded_columns:
        validated_column = validate_oracle_identifier(
            column_name,
            "excluded column"
        )

        validated_excluded_columns.append(
            validated_column
        )

    # ------------------------------------------------------------------
    # SECTION 5: DETERMINE INCLUDED TARGET COLUMNS
    # ------------------------------------------------------------------
    # Remove excluded columns while preserving the original source-column
    # order returned from Oracle metadata.
    included_columns = [
        column_name
        for column_name in validated_source_columns
        if column_name not in validated_excluded_columns
    ]

    # A target table must contain at least one column.
    if not included_columns:
        raise ValueError(
            "Target table must contain at least one source column."
        )

    # ------------------------------------------------------------------
    # SECTION 6: BUILD TARGET COLUMN LIST
    # ------------------------------------------------------------------
    # Example:
    #
    # CUSTOMER_ID, FULL_NAME, NATIONAL_ID, MONTHLY_INCOME
    column_list = ", ".join(
        included_columns
    )

    # ------------------------------------------------------------------
    # SECTION 7: BUILD CREATE TABLE STATEMENT
    # ------------------------------------------------------------------
    # WHERE 1 = 0 copies the selected column structure without copying
    # source-table rows.
    sql = f"""
        CREATE TABLE {target_schema}.{target_table}
        AS
        SELECT {column_list}
        FROM {source_schema}.{source_table}
        WHERE 1 = 0
    """

    cursor = connection.cursor()

    try:
        # ------------------------------------------------------------------
        # SECTION 8: CREATE EMPTY TARGET TABLE
        # ------------------------------------------------------------------
        cursor.execute(
            sql
        )

    finally:
        cursor.close()

    # ------------------------------------------------------------------
    # SECTION 9: RETURN INCLUDED COLUMN LIST
    # ------------------------------------------------------------------
    # ExecutionWorker and data_writer.py use exactly this column order
    # when inserting transformed rows.
    return included_columns


def drop_target_table(
    connection,
    target_schema,
    target_table
):
    # ------------------------------------------------------------------
    # SECTION 10: VALIDATE TARGET IDENTIFIERS
    # ------------------------------------------------------------------
    # DROP TABLE also uses dynamically constructed Oracle identifiers,
    # therefore they must be validated at this SQL boundary.
    target_schema = validate_oracle_identifier(
        target_schema,
        "target schema"
    )

    target_table = validate_oracle_identifier(
        target_table,
        "target table"
    )

    # ------------------------------------------------------------------
    # SECTION 11: BUILD DROP TABLE STATEMENT
    # ------------------------------------------------------------------
    sql = f"""
        DROP TABLE {target_schema}.{target_table}
    """

    cursor = connection.cursor()

    try:
        # ------------------------------------------------------------------
        # SECTION 12: DROP TARGET TABLE
        # ------------------------------------------------------------------
        cursor.execute(
            sql
        )

    finally:
        cursor.close()