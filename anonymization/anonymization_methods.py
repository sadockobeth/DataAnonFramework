import hashlib

def mask_value(value):
    if value is None:
        return None

    value = str(value)

    if len(value) <= 4:
        return "*" * len(value)

    return value[:2] + "*" * (len(value) - 4) + value[-2:]

"""
For example: value NID-100001 becomes something like: NI******01
"""

def tokenize_value(value):
    if value is None:
        return None

    value = str(value)

    token = hashlib.sha256(value.encode()).hexdigest()[:10]

    return f"TOKEN_{token}"