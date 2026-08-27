from anonymization.anonymization_methods import (
    mask_value,
    tokenize_value
)


def anonymize_row(row, rules):
    anonymized_row = row.copy()

    for column_name, strategy in rules.items():
        original_value = row[column_name]

        if strategy == "MASK":
            anonymized_row[column_name] = mask_value(original_value)

        elif strategy == "TOKENIZE":
            anonymized_row[column_name] = tokenize_value(original_value)

        else:
            raise ValueError(
                f"Unsupported strategy: {strategy}"
            )

    return anonymized_row