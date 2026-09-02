from pathlib import Path
import re
import pandas as pd


# ============================================================
# PATHS
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent

WORKBOOK_PATH = PROJECT_ROOT / "samples" / "daily_workbook.xlsx"


# ============================================================
# CONSTANTS
# ============================================================

SOURCE_SHEET_COLUMN = "SOURCE_SHEET"
WORKBOOK_NAME_COLUMN = "WORKBOOK_NAME"
SOURCE_ROW_COLUMN = "SOURCE_ROW"


COLUMN_RENAME_MAP = {
    "COLOUR": "COLOR",
    "AMOUNT": "AMT",
    "TOTAL": "AMT",
}


UNUSED_PATTERN = re.compile(r"^UNUSED_\d+$")


# ============================================================
# SIZE HEADERS
# ============================================================

SIZE_HEADERS = {
    "N/B",
    "0/3",
    "3/6",
    "6/9",
    "9/12",
    "2/3",
    "3/4",
    "4/5",
    "5/6",
    "6/7",
    "7/8",
    "0/6",
    "6/12",
    "12/18",
    "18/24",
    "2Y",
    "3Y",
    "S",
    "M",
    "L",
    "2XL",
    "BM",
    "RE",
    "P/M",
    "ALL",
    "SM",
    "OIL",
    "AD",
}


# ============================================================
# HEADER NORMALIZATION
# ============================================================

def normalize_header_value(value):

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("_", " ")
    )


# ============================================================
# TABLE TYPE DETECTION
# ============================================================

def identify_table_type(headers):

    normalized = {
        normalize_header_value(header)
        for header in headers
        if normalize_header_value(header)
    }

    # SHIFT TABLE
    if (
        "NAME" in normalized
        and "SHIFT" in normalized
        and (
            "SHIFT RATE" in normalized
            or "RATE PER SHIFT" in normalized
        )
    ):
        return "SHIFT"

    # PRODUCTION TABLE
    if (
        "NAME" in normalized
        and "STYLE" in normalized
        and "QTY" in normalized
        and "RATE" in normalized
        and (
            "AMOUNT" in normalized
            or "TOTAL" in normalized
            or "AMT" in normalized
        )
    ):
        return "PRODUCTION"

    return None


# ============================================================
# FIND ALL TABLE HEADERS
# ============================================================

def find_all_table_headers(raw_df):

    found_tables = []

    for row_index in range(len(raw_df)):

        row = raw_df.iloc[row_index]

        headers = [
            normalize_header_value(value)
            for value in row.tolist()
        ]

        table_type = identify_table_type(headers)

        if table_type is not None:

            found_tables.append(
                (
                    row_index,
                    table_type,
                    headers,
                )
            )

    return found_tables


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .upper()
    )


# ============================================================
# SHIFT STYLE / TYPE
# ============================================================

def extract_shift_style(value):

    value = clean_text(value)

    if not value:
        return ""

    if " - " in value:
        return value.split(" - ", 1)[0].strip()

    return value


def extract_shift_type(value):

    value = clean_text(value)

    if not value:
        return ""

    if " - " in value:
        return value.split(" - ", 1)[1].strip()

    return ""


# ============================================================
# SIZE COLUMN DETECTION
# ============================================================

def find_size_columns_from_headers(header_row_values, size_row_values=None):

    size_columns = []

    # --------------------------------------------------------
    # First check the actual header row
    # --------------------------------------------------------

    for index, value in enumerate(header_row_values):

        header = normalize_header_value(value)

        if header in SIZE_HEADERS:

            size_columns.append(
                (index, header)
            )

    # --------------------------------------------------------
    # Then check the row immediately below the header.
    #
    # This is important because the factory Excel format uses:
    #
    # Row 1 -> DATE NAME STYLE ... QTY RATE AMT
    # Row 2 ->              2/3 0/6 3/6 ...
    # --------------------------------------------------------

    if size_row_values is not None:

        for index, value in enumerate(size_row_values):

            size = normalize_header_value(value)

            if size in SIZE_HEADERS:

                # Do not duplicate a size already found
                already_exists = any(
                    existing_index == index
                    for existing_index, _
                    in size_columns
                )

                if not already_exists:

                    size_columns.append(
                        (index, size)
                    )

    return size_columns


# ============================================================
# CALCULATE QTY FROM SIZE COLUMNS
# ============================================================

def calculate_qty_from_sizes(table_df, size_columns):

    qty = pd.Series(
        0.0,
        index=table_df.index,
        dtype="float64"
    )

    for column in size_columns:

        if column not in table_df.columns:
            continue

        numeric_values = pd.to_numeric(
            table_df[column],
            errors="coerce"
        ).fillna(0)

        qty += numeric_values

    return qty


# ============================================================
# EXTRACT TABLE
# ============================================================

def extract_table(
    raw_df,
    header_row,
    next_header_row,
    sheet_name,
    workbook_name,
    table_type,
):

    # --------------------------------------------------------
    # MAIN HEADER ROW
    # --------------------------------------------------------

    main_headers = raw_df.iloc[
        header_row
    ].tolist()

    normalized_headers = [
        normalize_header_value(value)
        for value in main_headers
    ]

    detected_type = identify_table_type(
        normalized_headers
    )

    if detected_type is not None:
        table_type = detected_type

    # --------------------------------------------------------
    # POSSIBLE SIZE HEADER ROW
    # --------------------------------------------------------

    size_header_row = None

    candidate_row = header_row + 1

    if candidate_row < len(raw_df):

        candidate_values = raw_df.iloc[
            candidate_row
        ].tolist()

        candidate_sizes = [
            normalize_header_value(value)
            for value in candidate_values
            if normalize_header_value(value) in SIZE_HEADERS
        ]

        if candidate_sizes:

            size_header_row = candidate_row

    size_row_values = None

    if size_header_row is not None:

        size_row_values = raw_df.iloc[
            size_header_row
        ].tolist()

    # --------------------------------------------------------
    # BUILD FINAL HEADERS
    # --------------------------------------------------------

    final_headers = []

    for index, header in enumerate(main_headers):

        header = normalize_header_value(header)

        # ----------------------------------------------------
        # If the main header is empty, check whether the
        # second row contains a SIZE header at this position.
        # ----------------------------------------------------

        if not header and size_row_values is not None:

            possible_size = normalize_header_value(
                size_row_values[index]
            )

            if possible_size in SIZE_HEADERS:

                header = possible_size

        # ----------------------------------------------------
        # Normal header
        # ----------------------------------------------------

        if header:

            header = COLUMN_RENAME_MAP.get(
                header,
                header
            )

            final_headers.append(header)

        else:

            final_headers.append(
                f"UNUSED_{index}"
            )

    # --------------------------------------------------------
    # FIND SIZE COLUMNS
    # --------------------------------------------------------

    size_column_pairs = find_size_columns_from_headers(
        main_headers,
        size_row_values
    )

    size_columns = [
        size_name
        for _, size_name in size_column_pairs
        if size_name in final_headers
    ]

    size_columns = list(
        dict.fromkeys(size_columns)
    )

    print(
        f"SIZE COLUMNS FOUND: {size_columns}"
    )

    # --------------------------------------------------------
    # DATA START
    # --------------------------------------------------------

    data_start = header_row + 1

    # If a size-header row exists, skip it.
    if size_header_row is not None:

        data_start = size_header_row + 1

    # --------------------------------------------------------
    # DATA END
    # --------------------------------------------------------

    if next_header_row is not None:

        data_end = next_header_row

    else:

        data_end = len(raw_df)

    if data_start >= data_end:

        return pd.DataFrame()

    # --------------------------------------------------------
    # EXTRACT DATA
    # --------------------------------------------------------

    table_df = raw_df.iloc[
        data_start:data_end
    ].copy()

    # Make sure the number of headers matches columns
    if len(final_headers) < table_df.shape[1]:

        extra_columns = table_df.shape[1] - len(final_headers)

        for i in range(extra_columns):

            final_headers.append(
                f"UNUSED_EXTRA_{i}"
            )

    elif len(final_headers) > table_df.shape[1]:

        final_headers = final_headers[
            :table_df.shape[1]
        ]

    table_df.columns = final_headers

    # --------------------------------------------------------
    # SOURCE INFORMATION
    # --------------------------------------------------------

    table_df["SOURCE_ROW"] = (
        table_df.index + 1
    )

    table_df["SOURCE_SHEET"] = sheet_name

    table_df["WORKBOOK_NAME"] = workbook_name

    # --------------------------------------------------------
    # REMOVE COMPLETELY EMPTY ROWS
    # --------------------------------------------------------

    table_df = table_df.dropna(
        how="all"
    )

    if table_df.empty:
        return table_df

    # --------------------------------------------------------
    # NAME REQUIRED
    # --------------------------------------------------------

    if "NAME" in table_df.columns:

        table_df = table_df[
            table_df["NAME"].notna()
            &
            table_df["NAME"]
            .astype(str)
            .str.strip()
            .ne("")
        ]

    if table_df.empty:
        return table_df

    # ========================================================
    # SHIFT TABLE
    # ========================================================

    if table_type == "SHIFT":

        if "STYLE/ITEM" in table_df.columns:

            table_df["STYLE"] = (
                table_df["STYLE/ITEM"]
                .apply(extract_shift_style)
            )

            if "TYPE" not in table_df.columns:

                table_df["TYPE"] = (
                    table_df["STYLE/ITEM"]
                    .apply(extract_shift_type)
                )

    # ========================================================
    # TEXT COLUMNS
    # ========================================================

    text_columns = [
        "NAME",
        "STYLE",
        "DESCRIPTION",
        "TYPE",
        "COLOR",
        "OPERATION",
        "DEPARTMENT",
        "WORKER TYPE",
        "CONTRACTOR",
        "STYLE/ITEM",
    ]

    for column in text_columns:

        if column in table_df.columns:

            table_df[column] = (
                table_df[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

    # ========================================================
    # NUMERIC COLUMNS
    # ========================================================

    numeric_columns = [
        "QTY",
        "RATE",
        "AMT",
        "SHIFT",
        "SHIFT RATE",
        "DAILY SALARY",
    ]

    for column in numeric_columns:

        if column in table_df.columns:

            table_df[column] = pd.to_numeric(
                table_df[column],
                errors="coerce"
            )

    # ========================================================
    # SIZE QUANTITY CALCULATION
    # ========================================================

    if size_columns and table_type == "PRODUCTION":

        calculated_qty = (
            calculate_qty_from_sizes(
                table_df,
                size_columns
            )
        )

        # Existing QTY from Excel
        if "QTY" in table_df.columns:

            existing_qty = pd.to_numeric(
                table_df["QTY"],
                errors="coerce"
            )

            # Use calculated size total when available.
            #
            # If no size values exist for that row,
            # preserve the original QTY.
            valid_calculated = calculated_qty > 0

            table_df["QTY"] = existing_qty

            table_df.loc[
                valid_calculated,
                "QTY"
            ] = calculated_qty

        else:

            table_df["QTY"] = calculated_qty

    # ========================================================
    # SIZE COLUMNS -> NUMERIC
    # ========================================================

    for size_column in size_columns:

        if size_column in table_df.columns:

            table_df[size_column] = pd.to_numeric(
                table_df[size_column],
                errors="coerce"
            ).fillna(0)

    # ========================================================
    # SIZE COLUMN
    # ========================================================

    if "SIZE" in table_df.columns:

        table_df["SIZE"] = (
            table_df["SIZE"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # ========================================================
    # DATE
    # ========================================================

    if "DATE" in table_df.columns:

        table_df["DATE"] = pd.to_datetime(
            table_df["DATE"],
            errors="coerce",
            dayfirst=True
        )

    # ========================================================
    # TABLE TYPE
    # ========================================================

    table_df["TABLE_TYPE"] = table_type

    return table_df.reset_index(
        drop=True
    )


# ============================================================
# LOAD AND CLEAN ALL SHEETS
# ============================================================

def load_and_clean_all_sheets(workbook_path):

    workbook_path = Path(
        workbook_path
    )

    if not workbook_path.exists():

        raise FileNotFoundError(
            f"Workbook not found: {workbook_path}"
        )

    all_sheets = pd.read_excel(
        workbook_path,
        sheet_name=None,
        header=None,
        engine="openpyxl"
    )

    all_tables = []

    for sheet_name, raw_df in all_sheets.items():

        print()
        print("=" * 60)
        print(
            f"SCANNING SHEET: {sheet_name}"
        )
        print("=" * 60)

        table_infos = find_all_table_headers(
            raw_df
        )

        if not table_infos:

            print(
                "No recognized table found."
            )

            continue

        for table_number, (
            header_row,
            table_type,
            headers,
        ) in enumerate(
            table_infos,
            start=1
        ):

            print()
            print(
                f"Table {table_number}"
            )

            print(
                f"Header row : {header_row}"
            )

            print(
                f"Table type : {table_type}"
            )

            print(
                f"Headers    : {headers}"
            )

            # ------------------------------------------------
            # Find next table header
            # ------------------------------------------------

            later_headers = [
                info[0]
                for info in table_infos
                if info[0] > header_row
            ]

            next_header_row = (
                min(later_headers)
                if later_headers
                else None
            )

            # ------------------------------------------------
            # Extract
            # ------------------------------------------------

            table_df = extract_table(
                raw_df=raw_df,
                header_row=header_row,
                next_header_row=next_header_row,
                sheet_name=sheet_name,
                workbook_name=workbook_path.name,
                table_type=table_type,
            )

            if table_df.empty:
                continue

            all_tables.append(
                table_df
            )

    # ========================================================
    # COMBINE TABLES
    # ========================================================

    if not all_tables:

        return pd.DataFrame()

    dataframe = pd.concat(
        all_tables,
        ignore_index=True,
        sort=False
    )

    # ========================================================
    # REMOVE EMPTY NAMES
    # ========================================================

    if "NAME" in dataframe.columns:

        dataframe = dataframe.loc[
            dataframe["NAME"].notna()
            &
            dataframe["NAME"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()

    # ========================================================
    # REQUIRED PARSER COLUMNS
    # ========================================================

    required_parser_columns = [
        "DATE",
        "NAME",
        "STYLE",
        "DESCRIPTION",
        "QTY",
        "RATE",
        "AMT",
        "SOURCE_SHEET",
        "WORKBOOK_NAME",
        "SOURCE_ROW",
        "TABLE_TYPE",
    ]

    for column in required_parser_columns:

        if column not in dataframe.columns:

            dataframe[column] = pd.NA

    # ========================================================
    # DATE
    # ========================================================

    dataframe["DATE"] = pd.to_datetime(
        dataframe["DATE"],
        errors="coerce",
        dayfirst=True
    )

    # ========================================================
    # TEXT
    # ========================================================

    for column in [
        "NAME",
        "STYLE",
        "DESCRIPTION",
        "TYPE",
        "COLOR",
        "OPERATION",
    ]:

        if column in dataframe.columns:

            dataframe[column] = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

    # ========================================================
    # NUMBERS
    # ========================================================

    for column in [
        "QTY",
        "RATE",
        "AMT",
        "SHIFT",
        "SHIFT RATE",
        "DAILY SALARY",
    ]:

        if column in dataframe.columns:

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce"
            )

    # ========================================================
    # SIZE
    # ========================================================

    if "SIZE" in dataframe.columns:

        dataframe["SIZE"] = (
            dataframe["SIZE"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # ========================================================
    # SOURCE INFORMATION
    # ========================================================

    dataframe["SOURCE_SHEET"] = (
        dataframe["SOURCE_SHEET"]
        .astype(str)
        .str.strip()
    )

    dataframe["WORKBOOK_NAME"] = (
        dataframe["WORKBOOK_NAME"]
        .astype(str)
        .str.strip()
    )

    dataframe["SOURCE_ROW"] = pd.to_numeric(
        dataframe["SOURCE_ROW"],
        errors="coerce"
    )

    return dataframe.reset_index(
        drop=True
    )


# ============================================================
# SAMPLE WORKBOOK
# ============================================================

def load_sample_workbook():

    return load_and_clean_all_sheets(
        WORKBOOK_PATH
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    dataframe = load_sample_workbook()

    print()
    print("=" * 60)
    print("PARSER RESULT")
    print("=" * 60)

    print(
        dataframe.head(20)
    )

    print()

    print(
        f"Rows: {len(dataframe)}"
    )

    print()

    print(
        f"Columns: {list(dataframe.columns)}"
    )

    # ========================================================
    # QTY CHECK
    # ========================================================

    print()
    print("=" * 60)
    print("QTY VALUES")
    print("=" * 60)

    display_columns = [
        "NAME",
        "STYLE",
        "QTY",
        "RATE",
        "AMT",
        "TABLE_TYPE",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in dataframe.columns
    ]

    print(
        dataframe[
            display_columns
        ].head(20)
    )

    # ========================================================
    # PRODUCTION QTY VALIDATION
    # ========================================================

    if "TABLE_TYPE" in dataframe.columns:

        production_df = dataframe[
            dataframe["TABLE_TYPE"]
            == "PRODUCTION"
        ].copy()

        if not production_df.empty:

            invalid_production_qty = (
                production_df["QTY"].isna()
                |
                (production_df["QTY"] <= 0)
            )

            print()
            print("=" * 60)
            print("PRODUCTION QTY VALIDATION")
            print("=" * 60)

            print(
                f"Production rows: {len(production_df)}"
            )

            print(
                f"Invalid production QTY rows: "
                f"{invalid_production_qty.sum()}"
            )

            if invalid_production_qty.any():

                print()
                print(
                    production_df.loc[
                        invalid_production_qty,
                        [
                            "SOURCE_SHEET",
                            "SOURCE_ROW",
                            "NAME",
                            "STYLE",
                            "DESCRIPTION",
                            "QTY",
                        ],
                    ]
                )

    # ========================================================
    # UNIQUE STYLES
    # ========================================================

    print()
    print("=" * 60)
    print("UNIQUE STYLES")
    print("=" * 60)

    if "STYLE" in dataframe.columns:

        print(
            sorted(
                x
                for x in dataframe["STYLE"].unique()
                if str(x).strip()
            )
        )

    # ========================================================
    # UNIQUE OPERATIONS
    # ========================================================

    print()
    print("=" * 60)
    print("UNIQUE OPERATIONS")
    print("=" * 60)

    if "OPERATION" in dataframe.columns:

        print(
            sorted(
                x
                for x in dataframe["OPERATION"].unique()
                if str(x).strip()
            )
        )

    # ========================================================
    # DATE RANGE
    # ========================================================

    print()
    print("=" * 60)
    print("DATE RANGE")
    print("=" * 60)

    if "DATE" in dataframe.columns:

        print(
            "From:",
            dataframe["DATE"].min()
        )

        print(
            "To:",
            dataframe["DATE"].max()
        )