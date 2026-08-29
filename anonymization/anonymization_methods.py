import hashlib
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from decimal import Decimal, ROUND_HALF_UP

# ----------------------------------------------------------------------
# MASKING
# ----------------------------------------------------------------------

def mask_email(value):
    username, domain = value.split("@", 1)

    if len(username) <= 2:
        masked_username = "*" * len(username)
    else:
        masked_username = username[0] + "*" * (len(username) - 2) + username[-1]

    return f"{masked_username}@{domain}"


def mask_value(value):
    if value is None:
        return None

    value = str(value)

    # Intelligent email masking
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        return mask_email(value)

    # Generic masking
    if len(value) <= 4:
        return "*" * len(value)

    return value[:2] + "*" * (len(value) - 4) + value[-2:]


# ----------------------------------------------------------------------
# TOKENIZATION
# ----------------------------------------------------------------------

def tokenize_value(value):
    if value is None:
        return None

    value = str(value)
    token = hashlib.sha256(value.encode()).hexdigest()[:10]

    return f"TOKEN_{token}"


# ----------------------------------------------------------------------
# DATE SHIFT
# ----------------------------------------------------------------------

def shift_date(value, max_days=30):
    if value is None:
        return None

    if not isinstance(value, (date, datetime)):
        raise ValueError(
            f"DATE_SHIFT requires a date value. Received: {value}"
        )

    hash_number = int(
        hashlib.sha256(str(value).encode()).hexdigest()[:8],
        16
    )

    shift_days = (hash_number % (max_days * 2 + 1)) - max_days

    if shift_days == 0:
        shift_days = 1

    return value + timedelta(days=shift_days)


# ----------------------------------------------------------------------
# GENERALIZATION
# ----------------------------------------------------------------------

def generalize_amount(value):
    if value is None:
        return None

    amount = Decimal(str(value))

    # Remember whether the original amount was negative.
    is_negative = amount < 0

    # Work with the positive magnitude only.
    absolute_amount = abs(amount)

    # Zero remains zero.
    if absolute_amount == 0:
        return amount

    # Equivalent to FLOOR(LOG(10, value)) in Oracle,
    # but applied to the absolute amount.
    magnitude = absolute_amount.adjusted()

    if absolute_amount < Decimal("1e10"):
        # Round to one significant digit.
        rounding_unit = Decimal(f"1e{magnitude}")
    else:
        # Round to two significant digits.
        rounding_unit = Decimal(f"1e{magnitude - 1}")

    generalized_amount = absolute_amount.quantize(
        rounding_unit,
        rounding=ROUND_HALF_UP
    )

    # Restore the negative sign if the original value was negative.
    if is_negative:
        generalized_amount = -generalized_amount

    return generalized_amount

# ----------------------------------------------------------------------
# PERTURBATION
# ----------------------------------------------------------------------

def perturb_amount(value, max_percentage=5):
    if value is None:
        return None

    try:
        amount = Decimal(str(value))
    except Exception:
        raise ValueError(
            f"PERTURBATION requires a numeric value. Received: {value}"
        )

    hash_number = int(hashlib.sha256(str(value).encode()).hexdigest()[:8],16)

    adjustment = (
        hash_number % (max_percentage * 2 + 1)
    ) - max_percentage

    if adjustment == 0:
        adjustment = 1

    percentage = Decimal(adjustment) / Decimal("100")

    return amount * (Decimal("1") + percentage)