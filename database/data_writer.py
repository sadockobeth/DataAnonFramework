"""
Module: data_writer.py

Purpose:
Writes transformed data into Oracle target tables.

Main responsibilities:
- Validate Oracle schema, table, and column identifiers before dynamic SQL.
- Insert individual transformed rows when required.
- Insert multiple transformed rows efficiently using executemany().
- Build INSERT statements dynamically from the target column list.
- Use bind variables for transformed row values.
- Support both the existing CLI workflow and optimized GUI batch execution.

This module does not decide how values should be anonymized and
does not commit or roll back database transactions.
"""

from validation.oracle_identifier_validator import validate_oracle_identifier


def validate_insert_identifiers(
    schema_name,
    table_name,
    included_columns
):
    # ------------------------------------------------------------------
    # SECTION 1: VALIDATE TARGET SCHEMA
    # ------------------------------------------------------------------
    # Dynamic SQL identifiers cannot be passed as normal Oracle bind
    # variables, therefore validate them before SQL construction.
    validated_schema = validate_oracle_identifier(
        schema_name,
        "target schema"
    )

    # ------------------------------------------------------------------
    # SECTION 2: VALIDATE TARGET TABLE
    # ------------------------------------------------------------------
    validated_table = validate_oracle_identifier(
        table_name,
        "target table"
    )

    # ------------------------------------------------------------------
    # SECTION 3: VALIDATE TARGET COLUMNS
    # ------------------------------------------------------------------
    validated_columns = []

    for column_name in included_columns:
        validated_column = validate_oracle_identifier(
            column_name,
            "target column"
        )

        validated_columns.append(
            validated_column
        )

    if not validated_columns:
        raise ValueError(
            "At least one target column is required for insert."
        )

    return (
        validated_schema,
        validated_table,
        validated_columns
    )


def insert_row(
    connection,
    schema_name,
    table_name,
    row,
    included_columns
):
    # ------------------------------------------------------------------
    # SECTION 4: VALIDATE INSERT IDENTIFIERS
    # ------------------------------------------------------------------
    # Keep insert_row() safe for the existing CLI workflow even when it
    # is called independently of configuration_validator.py.
    schema_name, table_name, included_columns = validate_insert_identifiers(
        schema_name,
        table_name,
        included_columns
    )

    # ------------------------------------------------------------------
    # SECTION 5: BUILD SINGLE-ROW INSERT STATEMENT
    # ------------------------------------------------------------------
    column_list = ", ".join(
        included_columns
    )

    # Create positional bind variables such as:
    #
    # :1, :2, :3, :4
    bind_list = ", ".join(
        f":{position}"
        for position in range(
            1,
            len(included_columns) + 1
        )
    )

    # Extract values in exactly the same order as the columns appearing
    # in the INSERT statement.
    values = [
        row[column_name]
        for column_name in included_columns
    ]

    sql = f"""
        INSERT INTO {schema_name}.{table_name}
        ({column_list})
        VALUES ({bind_list})
    """

    cursor = connection.cursor()

    try:
        # ------------------------------------------------------------------
        # SECTION 6: INSERT ONE TRANSFORMED ROW
        # ------------------------------------------------------------------
        # Row values are safely supplied through Oracle bind variables.
        cursor.execute(
            sql,
            values
        )

    finally:
        cursor.close()


def insert_rows_batch(
    connection,
    schema_name,
    table_name,
    rows,
    included_columns
):
    # ------------------------------------------------------------------
    # SECTION 7: VALIDATE BATCH
    # ------------------------------------------------------------------
    # Nothing needs to be written when the supplied batch is empty.
    if not rows:
        return

    # ------------------------------------------------------------------
    # SECTION 8: VALIDATE INSERT IDENTIFIERS
    # ------------------------------------------------------------------
    # Schema, table, and column names are validated before any dynamic
    # INSERT statement is constructed.
    schema_name, table_name, included_columns = validate_insert_identifiers(
        schema_name,
        table_name,
        included_columns
    )

    # ------------------------------------------------------------------
    # SECTION 9: BUILD BATCH INSERT STATEMENT
    # ------------------------------------------------------------------
    # The same INSERT statement is used for every transformed row.
    column_list = ", ".join(
        included_columns
    )

    # Create positional bind variables such as:
    #
    # :1, :2, :3, :4
    bind_list = ", ".join(
        f":{position}"
        for position in range(
            1,
            len(included_columns) + 1
        )
    )

    sql = f"""
        INSERT INTO {schema_name}.{table_name}
        ({column_list})
        VALUES ({bind_list})
    """

    # ------------------------------------------------------------------
    # SECTION 10: PREPARE BATCH VALUES
    # ------------------------------------------------------------------
    # executemany() expects multiple sets of bind values.
    #
    # Example:
    #
    # [
    #     (1001, "TOKEN_A", "NI*****01"),
    #     (1002, "TOKEN_B", "NI*****02"),
    #     (1003, "TOKEN_C", "NI*****03")
    # ]
    values = []

    for row in rows:
        values.append(
            tuple(
                row[column_name]
                for column_name in included_columns
            )
        )

    # ------------------------------------------------------------------
    # SECTION 11: INSERT COMPLETE BATCH
    # ------------------------------------------------------------------
    # executemany() sends all prepared rows to Oracle through one batch
    # DML operation instead of calling execute() for every individual row.
    cursor = connection.cursor()

    try:
        cursor.executemany(
            sql,
            values
        )

    finally:
        cursor.close()