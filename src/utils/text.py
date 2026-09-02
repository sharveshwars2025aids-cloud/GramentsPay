import re


def normalize_name(value: str) -> str:
    """
    Normalizes master data names.

    Examples
    --------
    " overlock "
        -> "OVERLOCK"

    "Power Table"
        -> "POWER TABLE"
    """

    return value.strip().upper()


def normalize_alias(value: str) -> str:
    """
    Normalizes operation aliases.

    Examples
    --------
    " o/l "      -> "O/L"
    "O / L"      -> "O/L"
    "f / l"      -> "F/L"
    " S/N "      -> "S/N"
    """

    value = value.strip().upper()

    # Remove spaces around separators like /, -, +
    value = re.sub(r"\s*([/\-+])\s*", r"\1", value)

    return value