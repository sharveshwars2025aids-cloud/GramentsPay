from pathlib import Path
import pandas as pd


def main():
    
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    excel_path = project_root / "samples" / "daily_workbook.xlsx"

    try:
       
        df = pd.read_excel(excel_path, sheet_name=0, engine="openpyxl", header=1)

        print("Raw columns before cleaning:")
        print(list(df.columns))
        print()

        size_row = df.iloc[0]

        rename_map = {}
        for col_name, size_value in zip(df.columns, size_row):

            if str(col_name).startswith("Unnamed"):

                if pd.notna(size_value):
                    rename_map[col_name] = str(size_value)

        df = df.rename(columns=rename_map)

        df = df.drop(index=0).reset_index(drop=True)

        df = df.dropna(how="all").reset_index(drop=True)

        df = df.fillna("")

        df = df[df["NAME"] != ""]

        df = df.reset_index(drop=True)

        print("Cleaned columns:")
        print(list(df.columns))
        print()

        print("Cleaned DataFrame:")
        print(df)

        print("\nTotal Records:", len(df))

        print("\nEmployees:")
        for emp in df["NAME"].unique():
            print("-", emp)

        print("\nStyles:")
        for style in df["STYLE"].unique():
            if style != "":
                print("-", style)

    except FileNotFoundError:
        print("ERROR: Could not find the Excel file.")
        print(f"Expected it here: {excel_path}")

    except Exception as e:
        print("ERROR: Something went wrong while processing the Excel file.")
        print(f"Details: {e}")


if __name__ == "__main__":
    main()