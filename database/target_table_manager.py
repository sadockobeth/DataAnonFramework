def create_target_table(
    connection,
    source_schema,
    source_table,
    target_schema,
    target_table,
    source_columns,
    excluded_columns
):
    included_columns = [
        column
        for column in source_columns
        if column not in excluded_columns
    ]

    if not included_columns:
        raise ValueError("Cannot exclude all columns from target table.")

    column_list = ", ".join(included_columns)

    sql = f"""
        CREATE TABLE {target_schema}.{target_table}
        AS
        SELECT {column_list}
        FROM {source_schema}.{source_table}
        WHERE 1 = 0
    """

    cursor = connection.cursor()

    try:
        cursor.execute(sql)
    finally:
        cursor.close()

    return included_columns


def drop_target_table(
    connection,
    target_schema,
    target_table
):
    sql = f"""
        DROP TABLE {target_schema}.{target_table} PURGE
    """

    cursor = connection.cursor()

    try:
        cursor.execute(sql)
    finally:
        cursor.close()