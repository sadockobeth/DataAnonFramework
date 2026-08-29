def get_first_row(connection, schema_name, table_name):
    cursor = connection.cursor()

    try:
        sql = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            FETCH FIRST 1 ROW ONLY
        """

        cursor.execute(sql)

        row = cursor.fetchone()

        if row is None:
            return None

        column_names = [
            column[0]
            for column in cursor.description
        ]

        return dict(zip(column_names, row))

    finally:
        cursor.close()

"""
Possible output from get_first_row function
{
    "CUSTOMER_ID": 1001,
    "FULL_NAME": "Amina Hassan",
    "NATIONAL_ID": "NID-100001",
    "PHONE_NUMBER": "0712000001"
}
"""

def get_rows(connection, schema_name, table_name, row_limit):
    cursor = connection.cursor()

    try:
        sql = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            FETCH FIRST {row_limit} ROWS ONLY
        """

        cursor.execute(sql)

        column_names = [column[0] for column in cursor.description]

        rows = []

        for row in cursor:
            rows.append(dict(zip(column_names, row)))

        return rows

    finally:
        cursor.close()


"""
Returns a list of row dictionaries, for example
[
    {
        "CUSTOMER_ID": 1001,
        "FULL_NAME": "Amina Hassan"
    },
    {
        "CUSTOMER_ID": 1002,
        "FULL_NAME": "John Mrema"
    },
    {
        "CUSTOMER_ID": 1003,
        "FULL_NAME": "Neema Joseph"
    }
]
"""


def read_rows_in_batches(
    connection,
    schema_name,
    table_name,
    batch_size=1000
):
    cursor = connection.cursor()

    try:
        sql = f"""
            SELECT *
            FROM {schema_name}.{table_name}
        """

        cursor.execute(sql)

        column_names = [column[0] for column in cursor.description]

        while True:
            rows = cursor.fetchmany(batch_size)

            if not rows:
                break

            batch = []

            for row in rows:
                batch.append(
                    dict(zip(column_names, row))
                )

            yield batch

    finally:
        cursor.close()