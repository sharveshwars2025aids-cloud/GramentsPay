import pandas as pd

REQUIRED_COLUMNS = [
    "DATE",
    "NAME",
    "STYLE",
    "DESCRIPTION",
    "QTY",
    "RATE",
    "AMT",
]


def validate_empty_dataframe(dataframe):

    if dataframe.empty:
        raise ValueError("The uploaded Excel file is empty.")
def validate_required_columns(dataframe):

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )


def validate_employee_names(dataframe):

    dataframe["NAME"] = (
        dataframe["NAME"]
        .astype(str)
        .str.strip()
    )

    invalid_rows = dataframe[
        dataframe["NAME"] == ""
    ]

    if not invalid_rows.empty:
        raise ValueError(
            f"{len(invalid_rows)} row(s) have empty employee names."
        )

def validate_style_numbers(dataframe):

    if "TABLE_TYPE" in dataframe.columns:
        production = dataframe[
            dataframe["TABLE_TYPE"].astype(str).str.upper() == "PRODUCTION"
        ]
    else:
        production = dataframe

    invalid_rows = production[
        production["STYLE"].isna()
        | (production["STYLE"].astype(str).str.strip().str.upper().isin(["", "NAN"]))
    ]

    if not invalid_rows.empty:
        raise ValueError(
            f"{len(invalid_rows)} production row(s) have empty style numbers."
        )



def validate_dates(dataframe):

    try:
        pd.to_datetime(dataframe["DATE"])
    except Exception:
        raise ValueError("One or more dates are invalid.")


def validate_numeric_columns(dataframe):

    # -----------------------------------------
    # PRODUCTION WORKERS
    # -----------------------------------------
    production = dataframe[
        dataframe["TABLE_TYPE"].astype(str).str.upper() == "PRODUCTION"
    ].copy()

    production_numeric_columns = [
        "QTY",
        "RATE",
        "AMT",
    ]

    for column in production_numeric_columns:

        values = pd.to_numeric(
            production[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"Column '{column}' contains invalid numbers."
            )

        if (values <= 0).any():
            raise ValueError(
                f"Column '{column}' must be greater than zero."
            )

    # -----------------------------------------
    # SHIFT WORKERS
    # -----------------------------------------
    shift = dataframe[
        dataframe["TABLE_TYPE"].astype(str).str.upper() == "SHIFT"
    ].copy()

    shift_numeric_columns = [
        "SHIFT",
        "SHIFT RATE",
        "DAILY SALARY",
    ]

    for column in shift_numeric_columns:

        values = pd.to_numeric(
            shift[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"Column '{column}' contains invalid numbers."
            )

        if (values <= 0).any():
            raise ValueError(
                f"Column '{column}' must be greater than zero."
            )


def validate_dataframe(dataframe):

    dataframe.columns = (
        dataframe.columns
        .str.strip()
        .str.upper()
    )

    dataframe.dropna(
        how="all",
        inplace=True,
    )

    validate_empty_dataframe(dataframe)

    validate_required_columns(dataframe)

    validate_employee_names(dataframe)

    validate_style_numbers(dataframe)

    validate_dates(dataframe)

    validate_numeric_columns(dataframe)

    return True