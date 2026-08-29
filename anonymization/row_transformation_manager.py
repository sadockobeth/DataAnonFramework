from anonymization.anonymization_methods import (
    mask_value,
    tokenize_value,
    shift_date,
    generalize_amount,
    perturb_amount
)


def transform_row(row, rules):
    transformed_row = row.copy()

    for column_name, strategy in rules.items():
        original_value = row[column_name]

        if strategy == "MASKING":
            transformed_row[column_name] = mask_value(original_value)

        elif strategy == "TOKENIZATION":
            transformed_row[column_name] = tokenize_value(original_value)

        elif strategy == "DATE_SHIFT":
            transformed_row[column_name] = shift_date(original_value)

        elif strategy == "GENERALIZATION":
            transformed_row[column_name] = generalize_amount(original_value)

        elif strategy == "PERTURBATION":
            transformed_row[column_name] = perturb_amount(original_value)

        else:
            raise ValueError(
                f"Unsupported strategy: {strategy}"
            )

    return transformed_row