"""
weekly_closing.py

Main entry point for generating the Weekly Closing.

Workflow

Import Workbook
        ↓
Validate Data
        ↓
Store in Database
        ↓
Calculate Salary
        ↓
Generate Weekly Closing Workbook
"""

from importer import import_workbook
from salary_engine import calculate_weekly_salary
from excel_generator import generate_weekly_closing
from template_mapper import WEEKLY_CLOSING_TEMPLATE


def weekly_closing():
    """
    Executes the complete weekly closing workflow.
    """

    try:

        print("=" * 60)
        print("GARMENT WEEKLY CLOSING")
        print("=" * 60)
        print()


        print("Importing workbook...")

        week_id = import_workbook()

        print(f"Workbook imported successfully.")
        print(f"Week ID : {week_id}")
        print()



        print("Calculating salaries...")

        salary_result = calculate_weekly_salary(week_id)

        if salary_result is None:

            print("Salary calculation failed.")

            return

        print("Salary calculation completed.")
        print()

 

        print("Generating Weekly Closing workbook...")

        file_path = generate_weekly_closing(
            week_id=week_id,
            template=WEEKLY_CLOSING_TEMPLATE,
        )

 

        print()
        print("=" * 60)
        print("WEEKLY CLOSING COMPLETED")
        print("=" * 60)

        print(f"Week ID                 : {week_id}")
        print(f"Employees               : {len(salary_result['employees'])}")
        print(f"Employee Salary Total   : {salary_result['total_salary']:.2f}")
        print(
            f"Contractor Commission   : "
            f"{salary_result['total_contractor_commission']:.2f}"
        )
        print(
            f"Factory Expenses        : "
            f"{salary_result['total_factory_expense']:.2f}"
        )

        grand_total = (
            salary_result["total_salary"]
            + salary_result["total_contractor_commission"]
            + salary_result["total_factory_expense"]
        )

        print(f"Grand Total             : {grand_total:.2f}")
        print()
        print(f"Weekly Closing File     : {file_path}")
        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print("WEEKLY CLOSING FAILED")
        print("=" * 60)
        print(error)


if __name__ == "__main__":

    weekly_closing()