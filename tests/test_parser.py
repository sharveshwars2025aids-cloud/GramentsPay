from pathlib import Path

import pandas as pd

def main():

    current_file = Path(__file__).resolve()

    
    project_root = current_file.parent.parent

    
    excel_path = project_root / "samples" / "daily_workbook.xlsx"

    print(f"Looking for Excel file at: {excel_path}\n")

    try:
 
        workbook = pd.ExcelFile(excel_path, engine="openpyxl")

        print("Sheet names found in this workbook:")
        for name in workbook.sheet_names:
            print(f"  - {name}")
        print()  

        first_sheet_name = workbook.sheet_names[0]
        print(f"Reading the first sheet: '{first_sheet_name}'\n")

        df = workbook.parse(first_sheet_name, header=1)

        size_headers = df.iloc[0]

        print("\nSize Headers:")
        print(size_headers)

        print("Column names in this sheet:")
        for col in df.columns:
            print(f"  - {col}")
        print()

        print("First 20 rows of data:")
        print(df.head(20).to_string())

    except FileNotFoundError:
       
        print("ERROR: Could not find the Excel file.")
        print(f"Expected it here: {excel_path}")
        print("Double-check that 'daily_workbook.xlsx' exists inside the 'samples' folder.")

    except Exception as e:
       
        print("ERROR: Something went wrong while reading the Excel file.")
        print(f"Details: {e}")


if __name__ == "__main__":
    main()