"""
Module: data_writer.py

Purpose:
Writes transformed data into Oracle target tables.

Main responsibilities:
- Insert individual transformed rows when required.
- Insert multiple transformed rows efficiently using executemany().
- Build INSERT statements dynamically from the target column list.
- Use bind variables when sending row values to Oracle.
- Support both the existing CLI workflow and optimized GUI batch execution.

This module does not decide how values should be anonymized and
does not commit or roll back database transactions.
"""


def insert_row(connection, schema_name, table_name, row, included_columns):
    # ------------------------------------------------------------------
    # SECTION 1: BUILD SINGLE-ROW INSERT STATEMENT
    # ------------------------------------------------------------------
    # This function is retained for compatibility with the existing CLI
    # workflow and other code that needs to insert one row at a time.
    column_list = ", ".join(included_columns)

    # Create positional bind variables such as:
    # :1, :2, :3, :4
    bind_list = ", ".join(f":{position}" for position in range(1, len(included_columns) + 1))

    # Extract values from the transformed row in exactly the same order
    # as the target columns appearing in the INSERT statement.
    values = [row[column_name] for column_name in included_columns]

    sql = f"""
        INSERT INTO {schema_name}.{table_name}
        ({column_list})
        VALUES ({bind_list})
    """

    cursor = connection.cursor()

    try:
        # execute() inserts one transformed row.
        cursor.execute(sql, values)

    finally:
        cursor.close()


def insert_rows_batch(connection, schema_name, table_name, rows, included_columns):
    # ------------------------------------------------------------------
    # SECTION 2: VALIDATE BATCH
    # ------------------------------------------------------------------
    # There is nothing to write if the supplied batch contains no rows.
    if not rows:
        return

    # ------------------------------------------------------------------
    # SECTION 3: BUILD BATCH INSERT STATEMENT
    # ------------------------------------------------------------------
    # The same INSERT statement is used for every row in the batch.
    column_list = ", ".join(included_columns)

    # Create positional bind variables such as:
    # :1, :2, :3, :4
    bind_list = ", ".join(f":{position}" for position in range(1, len(included_columns) + 1))

    sql = f"""
        INSERT INTO {schema_name}.{table_name}
        ({column_list})
        VALUES ({bind_list})
    """

    # ------------------------------------------------------------------
    # SECTION 4: PREPARE BATCH VALUES
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
        values.append(tuple(row[column_name] for column_name in included_columns))

    # ------------------------------------------------------------------
    # SECTION 5: INSERT COMPLETE BATCH
    # ------------------------------------------------------------------
    # executemany() sends all prepared rows to Oracle through one
    # batch DML operation instead of calling execute() for every row.
    cursor = connection.cursor()

    try:
        cursor.executemany(sql, values)

    finally:
        cursor.close()