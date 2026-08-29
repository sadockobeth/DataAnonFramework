from oracledb import DatabaseError

from database.oracle_connection import connect_to_oracle
from database.database_metadata import get_table_columns
from database.data_reader import read_rows_in_batches
from database.data_writer import insert_row
from database.target_table_manager import (
    create_target_table,
    drop_target_table
)
from anonymization.row_transformation_manager import transform_row


def main():
    # ------------------------------------------------------------------
    # SECTION 1: INITIALIZE DATABASE CONNECTION VARIABLE
    # ------------------------------------------------------------------
    # We start with None so that the finally block can safely check
    # whether a connection was successfully created before closing it.
    connection = None

    try:
        # ------------------------------------------------------------------
        # SECTION 2: CONNECT TO ORACLE DATABASE
        # ------------------------------------------------------------------
        # Establish the Oracle database connection that will be reused
        # throughout the anonymization process.
        print("=" * 70)
        print("DATA ANONYMIZATION FRAMEWORK")
        print("=" * 70)

        print("\nConnecting to Oracle...")
        connection = connect_to_oracle()
        print("Oracle connection successful.")

        # ------------------------------------------------------------------
        # SECTION 3: GET SOURCE TABLE INFORMATION
        # ------------------------------------------------------------------
        # Ask the user which schema and table contain the source data
        # that needs to be anonymized.
        print("\nSOURCE TABLE CONFIGURATION")
        print("-" * 70)

        source_schema = input(
            "Enter source schema: "
        ).strip().upper()

        source_table = input(
            "Enter source table: "
        ).strip().upper()

        # ------------------------------------------------------------------
        # SECTION 4: READ SOURCE TABLE METADATA
        # ------------------------------------------------------------------
        # Retrieve the source table columns from Oracle.
        # This also helps us confirm that the table exists.
        table_columns = get_table_columns(
            connection,
            source_schema,
            source_table
        )

        if not table_columns:
            print(
                f"\nTable {source_schema}.{source_table} "
                f"was not found."
            )
            return

        # Convert metadata into a simple list of column names.
        available_columns = [
            column["column_name"]
            for column in table_columns
        ]

        print("\nAvailable columns")
        print("-" * 70)

        for column_name in available_columns:
            print(column_name)

        # ------------------------------------------------------------------
        # SECTION 5: DEFINE AVAILABLE ANONYMIZATION STRATEGIES
        # ------------------------------------------------------------------
        # These are the anonymization strategies currently supported by
        # anonymization_methods.py and row_transformation_manager.py.
        #
        # MASKING
        #     Hides part of the original value.
        #
        # TOKENIZATION
        #     Replaces the original value with a deterministic token.
        #
        # DATE_SHIFT
        #     Moves a date forward or backward by a controlled number
        #     of days.
        #
        # GENERALIZATION
        #     Reduces the precision of a numeric value.
        #
        # PERTURBATION
        #     Slightly changes a numeric value while keeping it close
        #     to the original value.
        available_strategies = {
            "1": "MASKING",
            "2": "TOKENIZATION",
            "3": "DATE_SHIFT",
            "4": "GENERALIZATION",
            "5": "PERTURBATION"
        }

        print("\nAvailable anonymization strategies")
        print("-" * 70)

        for number, strategy in available_strategies.items():
            print(f"{number}. {strategy}")

        # ------------------------------------------------------------------
        # SECTION 6: BUILD ANONYMIZATION RULES
        # ------------------------------------------------------------------
        # The user selects a column and then chooses which anonymization
        # strategy should be applied to that column.
        #
        # Example result:
        #
        # rules = {
        #     "FULL_NAME": "TOKENIZATION",
        #     "NATIONAL_ID": "MASKING",
        #     "EMAIL_ADDRESS": "MASKING",
        #     "DATE_OF_BIRTH": "DATE_SHIFT",
        #     "MONTHLY_INCOME": "GENERALIZATION"
        # }
        rules = {}

        while True:
            column_name = input(
                "\nEnter column to anonymize "
                "(press Enter when finished): "
            ).strip().upper()

            # Pressing Enter without entering a column means
            # the user has finished defining anonymization rules.
            if not column_name:
                break

            # Reject a column that does not exist in the source table.
            if column_name not in available_columns:
                print(
                    f"Column {column_name} does not exist."
                )
                continue

            print("\nSelect anonymization strategy")
            print("-" * 70)

            for number, strategy in available_strategies.items():
                print(f"{number}. {strategy}")

            strategy_number = input(
                "Enter strategy number: "
            ).strip()

            # Ensure the selected strategy number is valid.
            if strategy_number not in available_strategies:
                print("Invalid strategy selection.")
                continue

            strategy = available_strategies[
                strategy_number
            ]

            # Store the selected column and its strategy.
            #
            # Example:
            #
            # rules["EMAIL_ADDRESS"] = "MASKING"
            rules[column_name] = strategy

            print(
                f"Added: {column_name} -> {strategy}"
            )

        # At least one column must be selected for anonymization.
        if not rules:
            print(
                "\nNo columns were selected for anonymization."
            )
            return

        # Display the final anonymization rules for confirmation.
        print("\nSelected anonymization rules")
        print("-" * 70)

        for column_name, strategy in rules.items():
            print(
                f"{column_name} -> {strategy}"
            )

        # ------------------------------------------------------------------
        # SECTION 7: GET OUT_PLACE TARGET CONFIGURATION
        # ------------------------------------------------------------------
        # OUT_PLACE means the source table remains unchanged and the
        # anonymized data is written into a separate target table.
        print("\nOUT_PLACE TARGET CONFIGURATION")
        print("-" * 70)

        target_schema = input(
            "Enter target schema: "
        ).strip().upper()

        # If the user does not provide a target table name,
        # use SOURCE_TABLE_ANON as the default.
        default_target_table = (
            f"{source_table}_ANON"
        )

        target_table = input(
            f"Enter target table "
            f"[{default_target_table}]: "
        ).strip().upper()

        if not target_table:
            target_table = default_target_table

        # ------------------------------------------------------------------
        # SECTION 8: GET COLUMNS TO EXCLUDE FROM TARGET TABLE
        # ------------------------------------------------------------------
        # Excluded columns will not exist in the OUT_PLACE target table.
        #
        # Example:
        #
        # REPORTINGDATE
        #
        # The target table will therefore be created without
        # REPORTINGDATE.
        excluded_input = input(
            "Enter columns to exclude from target "
            "(comma separated, press Enter for none): "
        )

        excluded_columns = [
            column.strip().upper()
            for column in excluded_input.split(",")
            if column.strip()
        ]

        # Validate that every excluded column exists in the source table.
        invalid_excluded_columns = [
            column
            for column in excluded_columns
            if column not in available_columns
        ]

        if invalid_excluded_columns:
            print(
                "\nInvalid excluded columns: "
                + ", ".join(
                    invalid_excluded_columns
                )
            )
            return

        # ------------------------------------------------------------------
        # SECTION 9: CHECK FOR RULE/EXCLUSION CONFLICTS
        # ------------------------------------------------------------------
        # A column cannot be selected for anonymization and also be
        # excluded from the target table.
        #
        # Example invalid request:
        #
        # FULL_NAME -> TOKENIZATION
        # Exclude FULL_NAME
        #
        # There is no reason to anonymize a column that will not exist
        # in the target table.
        conflicts = [
            column
            for column in rules
            if column in excluded_columns
        ]

        if conflicts:
            print(
                "\nThese columns cannot be both "
                "anonymized and excluded: "
                + ", ".join(conflicts)
            )
            return

        # ------------------------------------------------------------------
        # SECTION 10: CREATE OUT_PLACE TARGET TABLE
        # ------------------------------------------------------------------
        # Create an empty target table using the source table structure,
        # excluding columns the user does not want in the target.
        #
        # No source rows are copied during table creation.
        try:
            included_columns = create_target_table(
                connection,
                source_schema,
                source_table,
                target_schema,
                target_table,
                available_columns,
                excluded_columns
            )

        except DatabaseError as error:
            error_object = error.args[0]

            # ORA-00955 means an object with the target name
            # already exists in Oracle.
            if error_object.code != 955:
                raise

            print(
                f"\nTarget table "
                f"{target_schema}.{target_table} "
                f"already exists."
            )

            # Ask the user before dropping an existing target table.
            answer = input(
                "Drop existing target table? "
                "Type YES to continue: "
            ).strip().upper()

            if answer != "YES":
                print("Operation cancelled.")
                return

            # Drop the existing target table.
            drop_target_table(
                connection,
                target_schema,
                target_table
            )

            print(
                "Existing target table dropped."
            )

            # Recreate the empty target table.
            included_columns = create_target_table(
                connection,
                source_schema,
                source_table,
                target_schema,
                target_table,
                available_columns,
                excluded_columns
            )

        print(
            f"\nTarget table "
            f"{target_schema}.{target_table} "
            f"created successfully."
        )

        print(
            "Target columns: "
            + ", ".join(included_columns)
        )

        # ------------------------------------------------------------------
        # SECTION 11: INITIALIZE PROCESSING COUNTERS
        # ------------------------------------------------------------------
        # These variables allow us to monitor the number of batches and
        # rows processed during the anonymization operation.
        batch_number = 0
        total_rows = 0

        # ------------------------------------------------------------------
        # SECTION 12: READ SOURCE DATA IN BATCHES
        # ------------------------------------------------------------------
        # The source table is read in small batches rather than loading
        # the entire table into Python memory.
        #
        # batch_size=3 is intentionally small while learning/testing.
        # Later we can increase it, for example to 1000.
        for batch in read_rows_in_batches(
            connection,
            source_schema,
            source_table,
            batch_size=3
        ):
            batch_number += 1

            print(
                f"\nProcessing batch {batch_number} "
                f"({len(batch)} rows)"
            )

            # ------------------------------------------------------------------
            # SECTION 13: TRANSFORM AND INSERT EACH ROW IN THE BATCH
            # ------------------------------------------------------------------
            # Each source row is passed to the transformation manager.
            #
            # row_transformation_manager.py checks the strategy selected
            # for each column and calls the corresponding method from
            # anonymization_methods.py.
            #
            # Example:
            #
            # EMAIL_ADDRESS -> MASKING
            #     calls mask_value()
            #
            # FULL_NAME -> TOKENIZATION
            #     calls tokenize_value()
            #
            # DATE_OF_BIRTH -> DATE_SHIFT
            #     calls shift_date()
            #
            # MONTHLY_INCOME -> GENERALIZATION
            #     calls generalize_amount()
            for row in batch:
                transformed_row = transform_row(
                    row,
                    rules
                )

                # Write the transformed row into the target table.
                #
                # Only columns contained in included_columns are inserted.
                # Columns excluded earlier are therefore not written.
                insert_row(
                    connection,
                    target_schema,
                    target_table,
                    transformed_row,
                    included_columns
                )

                total_rows += 1

            print(
                f"Batch {batch_number} processed."
            )

        # ------------------------------------------------------------------
        # SECTION 14: COMMIT ALL INSERTED ROWS
        # ------------------------------------------------------------------
        # We commit only after every batch has completed successfully.
        #
        # This means all INSERT operations are treated as one transaction.
        #
        # If an error occurs before this point, the exception section below
        # performs a rollback of all uncommitted inserted rows.
        connection.commit()

        print("\n" + "=" * 70)
        print("ANONYMIZATION COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(
            f"Source table       : "
            f"{source_schema}.{source_table}"
        )

        print(
            f"Target table       : "
            f"{target_schema}.{target_table}"
        )

        print(
            f"Batches processed  : "
            f"{batch_number}"
        )

        print(
            f"Total rows inserted: "
            f"{total_rows}"
        )

    # ------------------------------------------------------------------
    # SECTION 15: HANDLE ERRORS
    # ------------------------------------------------------------------
    # If an error occurs before the final COMMIT, rollback all
    # uncommitted INSERT operations.
    #
    # Note:
    # CREATE TABLE and DROP TABLE are Oracle DDL operations and are
    # automatically committed by Oracle. Therefore, rollback affects
    # the inserted rows, not the already-created target table.
    except Exception as error:
        print("\nAn error occurred:")
        print(error)

        if connection is not None:
            connection.rollback()

            print(
                "All uncommitted inserts rolled back."
            )

    # ------------------------------------------------------------------
    # SECTION 16: CLOSE DATABASE CONNECTION
    # ------------------------------------------------------------------
    # This block runs whether processing succeeds or fails.
    # It ensures that the Oracle connection is always closed properly.
    finally:
        if connection is not None:
            connection.close()

            print(
                "\nOracle connection closed."
            )


# ----------------------------------------------------------------------
# PROGRAM ENTRY POINT
# ----------------------------------------------------------------------
# Python executes main() only when this file is run directly.
if __name__ == "__main__":
    main()