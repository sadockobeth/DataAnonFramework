def get_table_columns(connection, schema_name, table_name):
    cursor = connection.cursor()

    try:
        sql = """
            SELECT column_name, data_type, data_length, nullable
            FROM all_tab_columns
            WHERE owner = :schema_name
              AND table_name = :table_name
            ORDER BY column_id
        """

        cursor.execute(
            sql,
            schema_name=schema_name.upper(),
            table_name=table_name.upper()
        )

        columns = []

        for row in cursor:
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "data_length": row[2],
                "nullable": row[3]
            })

        return columns

    finally:
        cursor.close()

"""
After several rows, columns might look like:
[
    {
        "column_name": "CUSTOMER_ID",
        "data_type": "NUMBER",
        "data_length": 22,
        "nullable": "N"
    },
    {
        "column_name": "FULL_NAME",
        "data_type": "VARCHAR2",
        "data_length": 100,
        "nullable": "Y"
    },
    {
        "column_name": "NATIONAL_ID",
        "data_type": "VARCHAR2",
        "data_length": 50,
        "nullable": "Y"
    }
]
"""




def validate_columns(table_columns, selected_columns):

    available_columns = [column["column_name"].upper() for column in table_columns]

    invalid_columns = [column for column in selected_columns if column not in available_columns]

    return invalid_columns