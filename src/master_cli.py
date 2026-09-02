"""
master_cli.py

Command Line Interface for managing
Garments Automation master data.

Responsibilities

User
    ↓
CLI Menu
    ↓
master_data.py
    ↓
Database

This module contains NO SQL.
"""

from __future__ import annotations

import os

from master_data import (
    # Departments
    add_department,
    list_departments,
    update_department,
    delete_department,

    # Contractors
    add_contractor,
    list_contractors,
    update_contractor,
    delete_contractor,

    # Employees
    add_employee,
    list_employees,
    search_employee,
    update_employee,
    disable_employee,
    get_department,
    get_contractor,

    # Styles
    add_style,
    list_styles,
    update_style,
    disable_style,
    search_style,
    get_style,
    style_exists,

    add_operation,
    list_operations,
    search_operation,
    update_operation,
    disable_operation,
    get_operation,
    operation_exists,

    add_operation_alias,
    get_operation_alias,
    list_operation_aliases,
    delete_operation_alias,
    operation_alias_exists,

    # Style Rates
    add_style_operation_rate,
    get_style_operation_rates,
    update_style_operation_rate,
    delete_style_operation_rate,
)


# ==========================================================
# UTILITIES
# ==========================================================

def clear_screen() -> None:
    """
    Clears the terminal.
    """

    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    """
    Wait for user input.
    """

    input("\nPress ENTER to continue...")


def title(text: str) -> None:
    """
    Prints a page title.
    """

    clear_screen()

    print("=" * 60)
    print(text.center(60))
    print("=" * 60)
    print()


# ==========================================================
# MAIN MENU
# ==========================================================

def main_menu() -> str:

    title("GARMENTS AUTOMATION")

    print("1. Departments")
    print("2. Contractors")
    print("3. Employees")
    print("4. Styles")
    print("5. Operation")
    print("6. Rate Master")
    print("0. Exit")
    print()

    return input("Choice : ").strip()

# ==========================================================
# DEPARTMENTS MENU
# ==========================================================

def departments_menu() -> None:

    while True:

        title("DEPARTMENTS")

        print("1. Add Department")
        print("2. List Departments")
        print("3. Update Department")
        print("4. Delete Department")
        print("0. Back")
        print()

        choice = input("Choice : ").strip()

        try:

            if choice == "1":

                name = input(
                    "Department Name : "
                )

                add_department(name)

                print("\nDepartment added successfully.")

                pause()

            elif choice == "2":

                departments = list_departments()

                print()

                if not departments:

                    print("No departments found.")

                else:

                    for department in departments:

                        print(
                            f"{department['id']:>3}  "
                            f"{department['name']}"
                        )

                pause()

            elif choice == "3":

                old_name = input(
                    "Current Name : "
                )

                new_name = input(
                    "New Name : "
                )

                update_department(
                    old_name,
                    new_name,
                )

                print("\nDepartment updated.")

                pause()

            elif choice == "4":

                name = input(
                    "Department Name : "
                )

                delete_department(name)

                print("\nDepartment deleted.")

                pause()

            elif choice == "0":

                return

            else:

                print("\nInvalid choice.")

                pause()

        except Exception as error:

            print(f"\nError : {error}")

            pause()

# ==========================================================
# CONTRACTORS MENU
# ==========================================================

def contractors_menu() -> None:

    while True:

        title("CONTRACTORS")

        print("1. Add Contractor")
        print("2. List Contractors")
        print("3. Update Contractor")
        print("4. Delete Contractor")
        print("0. Back")
        print()

        choice = input("Choice : ").strip()

        try:

            if choice == "1":

                name = input(
                    "Contractor Name : "
                )

                commission = float(
                    input(
                        "Commission Per Shift : "
                    )
                )

                add_contractor(
                    name=name,
                    commission_rate=commission,
                )

                print("\nContractor added successfully.")

                pause()

            elif choice == "2":

                contractors = list_contractors()

                print()

                if not contractors:

                    print("No contractors found.")

                else:

                    print(
                        f"{'ID':<5}"
                        f"{'NAME':<20}"
                        f"{'COMMISSION':>12}"
                    )

                    print("-" * 40)

                    for contractor in contractors:

                        print(
                            f"{contractor['id']:<5}"
                            f"{contractor['name']:<20}"
                            f"{contractor['commission_rate']:>12.2f}"
                        )

                pause()

            elif choice == "3":

                old_name = input(
                    "Current Name : "
                )

                new_name = input(
                    "New Name : "
                )

                commission = float(
                    input(
                        "New Commission : "
                    )
                )

                update_contractor(
                    old_name,
                    new_name=new_name,
                    commission_rate=commission,
                )

                print("\nContractor updated.")

                pause()

            elif choice == "4":

                name = input(
                    "Contractor Name : "
                )

                delete_contractor(name)

                print("\nContractor deleted.")

                pause()

            elif choice == "0":

                return

            else:

                print("\nInvalid choice.")

                pause()

        except Exception as error:

            print(f"\nError : {error}")

            pause()

# ==========================================================
# EMPLOYEES MENU
# ==========================================================

def employees_menu() -> None:

    while True:

        title("EMPLOYEES")

        print("1. Add Employee")
        print("2. List Employees")
        print("3. Search Employee")
        print("4. Update Employee")
        print("5. Disable Employee")
        print("0. Back")
        print()

        choice = input("Choice : ").strip()

        try:

            if choice == "1":

                employee_code = input(
                    "Employee Code : "
                ).strip()

                name = input(
                    "Employee Name : "
                ).strip()

                department = input(
                    "Department : "
                ).strip()

                pay_type = input(
                    "Pay Type (PIECE/SHIFT) : "
                ).strip().upper()

                worker_type = input(
                    "Worker Type (HELPER/OPERATOR) : "
                ).strip().upper()

                contractor = input(
                    "Contractor (Leave blank if company worker) : "
                ).strip()

                if contractor == "":
                    contractor = None

                shift_rate = None

                if pay_type == "SHIFT":

                    shift_rate = float(
                        input(
                            "Shift Rate : "
                        )
                    )

                department_data = get_department(department)

                if department_data is None:
                    raise LookupError(
                        f"Department '{department}' not found."
                    )

                department_id = department_data["id"]

                contractor_id = None

                if contractor:

                    contractor_data = get_contractor(contractor)

                    if contractor_data is None:
                        raise LookupError(
                            f"Contractor '{contractor}' not found."
                        )

                    contractor_id = contractor_data["id"]

                if employee_code == "":
                    employee_code = None

                add_employee(
                    employee_code=employee_code,
                    name=name,
                    pay_type=pay_type,
                    department_id=department_id,
                    worker_type=worker_type,
                    contractor_id=contractor_id,
                    shift_rate=shift_rate,
                )
                print("\nEmployee added successfully.")

                pause()

            elif choice == "2":

                employees = list_employees()

                print()

                if not employees:

                    print("No employees found.")

                else:

                    print(
                        f"{'ID':<4}"
                        f"{'CODE':<12}"
                        f"{'NAME':<20}"
                        f"{'PAY':<8}"
                        f"{'WORKER':<12}"
                        f"{'STATUS':<10}"
                        f"{'DEPARTMENT':<15}"
                        f"{'CONTRACTOR':<18}"
                        f"{'SHIFT RATE':>12}"
                    )

                    print("-" * 118)

                    for employee in employees:

                        contractor = (
                            employee["contractor"]
                            if employee["contractor"]
                            else "-"
                        )

                        shift_rate = (
                            employee["shift_rate"]
                            if employee["shift_rate"] is not None
                            else "-"
                        )

                        code = (
                            employee["employee_code"]
                            if employee["employee_code"]
                            else "-"
                        )       

                        print(
                            f"{employee['id']:<4}"
                            f"{code:<12}"
                            f"{employee['name']:<20}"
                            f"{employee['pay_type']:<8}"
                            f"{employee['worker_type']:<12}"
                            f"{employee['status']:<10}"
                            f"{employee['department']:<15}"
                            f"{contractor:<18}"
                            f"{str(shift_rate):>12}"
                        )

                pause()

            elif choice == "3":

                keyword = input(
                    "Employee Name : "
                ).strip()

                employees = search_employee(keyword)

                print()

                if not employees:

                    print("No matching employees found.")

                else:

                    print(
                        f"{'ID':<4}"
                        f"{'CODE':<12}"
                        f"{'NAME':<20}"
                        f"{'PAY':<8}"
                        f"{'WORKER':<12}"
                        f"{'DEPARTMENT':<15}"
                        f"{'CONTRACTOR':<18}"
                        f"{'SHIFT RATE':>12}"
                    )

                    print("-" * 105)

                    for employee in employees:

                        code = (
                            employee["employee_code"]
                            if employee["employee_code"]
                            else "-"
                        )

                        contractor = (
                            employee["contractor"]
                            if employee["contractor"]
                            else "-"
                        )

                        shift_rate = (
                            employee["shift_rate"]
                            if employee["shift_rate"] is not None
                            else "-"
                        )

                        print(
                            f"{employee['id']:<4}"
                            f"{code:<12}"
                            f"{employee['name']:<20}"
                            f"{employee['pay_type']:<8}"
                            f"{employee['worker_type']:<12}"
                            f"{employee['department']:<15}"
                            f"{contractor:<18}"
                            f"{str(shift_rate):>12}"
                        )

                pause()
            elif choice == "4":

                current_name = input(
                    "Employee to update : "
                ).strip()

                results = search_employee(current_name)

                print()

                if not results:

                    print("Employee not found.")

                    pause()

                    continue

                employee = results[0]

                print(f"Current Name       : {employee['name']}")
                print(f"Current Code       : {employee['employee_code']}")
                print(f"Current Department : {employee['department']}")
                print(f"Current Pay Type   : {employee['pay_type']}")
                print(f"Current Worker Type: {employee['worker_type']}")
                print(f"Current Contractor : {employee['contractor']}")
                print(f"Current Shift Rate : {employee['shift_rate']}")

                new_name = input(
                    f"New Name [{employee['name']}] : "
                ).strip()

                employee_code = input(
                    f"Employee Code [{employee['employee_code'] or ''}] : "
                ).strip()

                department = input(
                    f"Department [{employee['department']}] : "
                ).strip()

                pay_type = input(
                    f"Pay Type [{employee['pay_type']}] : "
                ).strip().upper()

                worker_type = input(
                    f"Worker Type [{employee['worker_type']}] : "
                ).strip().upper()

                contractor = input(
                    f"Contractor [{employee['contractor'] or ''}] : "
                ).strip()

                shift_rate = input(
                    f"Shift Rate [{employee['shift_rate'] or ''}] : "
                ).strip()

                if new_name == "":
                    new_name = None

                if employee_code == "":
                    employee_code = None

                if department == "":
                    department = None

                if pay_type == "":
                    pay_type = None

                if worker_type == "":
                    worker_type = None

                if contractor == "":
                    contractor = None

                if shift_rate == "":
                    shift_rate = None
                else:
                    shift_rate = float(shift_rate)

                department_id = None

                if department is not None:

                    department_data = get_department(department)

                    if department_data is None:

                        raise LookupError(
                            f"Department '{department}' not found."
                        )           

                    department_id = department_data["id"]


                contractor_id = None

                if contractor is not None:

                    contractor_data = get_contractor(contractor)

                    if contractor_data is None:

                        raise LookupError(
                            f"Contractor '{contractor}' not found."
                        )

                    contractor_id = contractor_data["id"]


                update_employee(

                    current_name,

                    new_name=new_name,

                    employee_code=employee_code,

                    pay_type=pay_type,

                    department_id=department_id,

                    contractor_id=contractor_id,

                    worker_type=worker_type,

                    shift_rate=shift_rate,

                )

                confirm = input(
                    "\nSave changes? (Y/N): "
                ).strip().upper()

                if confirm != "Y":

                    print("\nUpdate cancelled.")

                    pause()

                    continue


                print("\nEmployee updated successfully.")

                pause()

                print()

            elif choice == "5":

                name = input(
                    "Employee Name : "
                ).strip()

                results = search_employee(name)

                print()

                if not results:

                    print("Employee not found.")

                    pause()

                    continue

                employee = results[0]

                print(f"Name       : {employee['name']}")
                print(f"Department : {employee['department']}")
                print(f"Pay Type   : {employee['pay_type']}")
                print(f"Status     : {employee['status']}")

                print()

                confirm = input(
                    "Disable this employee? (Y/N): "
                ).strip().upper()

                if confirm != "Y":

                    print("\nOperation cancelled.")

                    pause()

                    continue

                disable_employee(
                    employee["name"],
                )

                print("\nEmployee disabled successfully.")

                pause()

            elif choice == "0":

                return

            else:

                print("\nInvalid choice.")

                pause()

        except Exception as error:

            print(f"\nError : {error}")

            pause()

def styles_menu():

    while True:

        clear_screen()

        print("=" * 60)
        print("STYLES".center(60))
        print("=" * 60)

        print()
        print("1. Add Style")
        print("2. List Styles")
        print("3. Search Style")
        print("4. Update Style")
        print("5. Disable Style")
        print("0. Back")
        print()

        choice = input("Choice : ").strip()

        if choice == "0":
            return

        elif choice == "1":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_no:

                print("\nStyle Number is required.")

                pause()

                continue

            if style_exists(style_no):

                print("\nStyle already exists.")

                pause()

                continue

            style_name = input(
                "Style Name (Optional) : "
            ).strip()

            confirm = input(
                "\nSave Style? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nOperation cancelled.")

                pause()

                continue

            add_style(
                style_no=style_no,
                style_name=style_name or None,
            )

            print("\nStyle added successfully.")

            pause()
            
        elif choice == "2":

            styles = list_styles()

            print()

            if not styles:

                print("No styles found.")

                pause()

                continue

            print(
                f"{'ID':<5}"
                f"{'STYLE NO':<20}"
                f"{'STYLE NAME':<35}"
                f"{'STATUS':<12}"
            )

            print("-" * 72)

            for style in styles:

                style_name = (
                    style["style_name"]
                    if style["style_name"]
                    else "-"
                )

                print(
                    f"{style['id']:<5}"
                    f"{style['style_no']:<20}"
                    f"{style_name:<35}"
                    f"{style['status']:<12}"
                )       

            pause()

        elif choice == "3":

            keyword = input(
                "Search Style : "
            ).strip()

            results = search_style(
                keyword,
            )

            print()

            if not results:

                print("No matching styles found.")

                pause()

                continue

            print(
                f"{'ID':<5}"
                f"{'STYLE NO':<20}"
                f"{'STYLE NAME':<35}"
                f"{'STATUS':<12}"
            )

            print("-" * 72)

            for style in results:

                style_name = (
                    style["style_name"]
                    if style["style_name"]
                    else "-"
                )

                print(
                    f"{style['id']:<5}"
                    f"{style['style_no']:<20}"
                    f"{style_name:<35}"
                    f"{style['status']:<12}"
                )

            pause()
        elif choice == "4":

            current_style = input(
                "Style Number to update : "
            ).strip()

            style = get_style(current_style)

            print()

            if style is None:

                print("Style not found.")

                pause()

                continue

            print(f"Current Style Number : {style['style_no']}")
            print(f"Current Style Name   : {style['style_name']}")
            print(f"Current Status       : {style['status']}")

            print()

            new_style_no = input(
                f"New Style Number [{style['style_no']}] : "
            ).strip()

            style_name = input(
                f"Style Name [{style['style_name'] or ''}] : "
            ).strip()

            if new_style_no == "":
                new_style_no = None

            if style_name == "":
                style_name = None

            confirm = input(
                "\nSave changes? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nUpdate cancelled.")

                pause()

                continue

            update_style(
                current_style,
                new_style_no=new_style_no,
                style_name=style_name,
            )

            print("\nStyle updated successfully.")

            pause()

        elif choice == "5":

            style_no = input(
                "Style Number : "
            ).strip()

            style = get_style(style_no)

            print()

            if style is None:

                print("Style not found.")

                pause()

                continue

            print(f"Style Number : {style['style_no']}")
            print(f"Style Name   : {style['style_name']}")
            print(f"Status       : {style['status']}")

            if style["status"] == "inactive":

                print("\nStyle is already inactive.")

                pause()

                continue

            confirm = input(
                "\nDisable this style? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nOperation cancelled.")

                pause()

                continue

            disable_style(
                style["style_no"],
            )

            print("\nStyle disabled successfully.")

            pause()

        else:

            print("\nInvalid choice.")

            pause()

def operations_menu():

    while True:

        clear_screen()

        print("=" * 60)
        print("OPERATIONS".center(60))
        print("=" * 60)

        print("\n1. Add Operation")
        print("2. List Operations")
        print("3. Search Operation")
        print("4. Update Operation")
        print("5. Disable Operation")
        print("6. Manage Aliases")
        print("0. Back")

        choice = input("\nChoice : ").strip()

        if choice == "1":

            operation_name = input(
                "Operation Name : "
            ).strip()

            if not operation_name:

                print("\nOperation Name is required.")

                pause()

                continue

            if operation_exists(operation_name):

                print("\nOperation already exists.")

                pause()

                continue

            confirm = input(
                "\nSave Operation? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nOperation cancelled.")

                pause()

                continue

            add_operation(
                operation_name=operation_name,
            )

            print("\nOperation added successfully.")

            pause()

        elif choice == "2":

            operations = list_operations()

            print()

            if not operations:

                print("No operations found.")

                pause()

                continue

            print(
                f"{'ID':<4}"
                f"{'NAME':<25}"
                f"{'STATUS':<12}"
            )

            print("-" * 41)

            for operation in operations:

                print(
                    f"{operation['id']:<4}"
                    f"{operation['operation_name']:<25}"
                    f"{operation['status']:<12}"
                )

            pause()

            
        elif choice == "3":

            keyword = input(
                "Search Operation : "
            ).strip()

            operations = search_operation(
                keyword
            )

            print()

            if not operations:

                print("No matching operations found.")

                pause()

                continue

            print(
                f"{'ID':<4}"
                f"{'NAME':<25}"
                f"{'STATUS':<12}"
            )

            print("-" * 41)

            for operation in operations:

                print(
                    f"{operation['id']:<4}"
                    f"{operation['operation_name']:<25}"
                    f"{operation['status']:<12}"
                )

            pause()

        elif choice == "4":

            operation_name = input(
                "Operation : "
            ).strip()

            operation = get_operation(
                operation_name
            )

            if operation is None:

                print("\nOperation not found.")

                pause()

                continue

            print("\nLeave blank to keep current value.\n")

            print(
                f"Current Operation : {operation['operation_name']}"
            )

            new_name = input(
                "New Operation : "
            ).strip()

            if not new_name:

                new_name = None

            confirm = input(
                "\nUpdate this operation? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nUpdate cancelled.")

                pause()

                continue

            update_operation(
                operation_name,
                new_operation_name=new_name,
            )

            print("\nOperation updated successfully.")

            pause()

        elif choice == "5":

            operation_name = input(
                "Operation : "
            ).strip()

            operation = get_operation(
                operation_name
            )

            if operation is None:

                print("\nOperation not found.")

                pause()

                continue

            print()

            print(
                f"Operation : {operation['operation_name']}"
            )

            print(
                f"Status    : {operation['status']}"
            )

            confirm = input(
                "\nDisable this operation? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nOperation not disabled.")

                pause()

                continue

            disable_operation(
                operation_name
            )

            print("\nOperation disabled successfully.")

            pause()

        elif choice == "6":

            aliases_menu()

        elif choice == "0":

            break

        else:

            print("\nInvalid choice.")

            pause()

def aliases_menu():

    while True:

        clear_screen()

        print("=" * 60)
        print("OPERATION ALIASES".center(60))
        print("=" * 60)

        print("\n1. Add Alias")
        print("2. List Aliases")
        print("3. Delete Alias")
        print("0. Back")

        choice = input("\nChoice : ").strip()

        if choice == "1":

            operation_name = input(
                "Operation : "
            ).strip()

            operation = get_operation(
                operation_name
            )

            if operation is None:

                print("\nOperation not found.")

                pause()

                continue

            alias = input(
                "Alias : "
            ).strip()

            if not alias:

                print("\nAlias is required.")

                pause()

                continue

            if operation_alias_exists(alias):

                print("\nAlias already exists.")

                pause()

                continue

            confirm = input(
                "\nSave Alias? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nAlias not saved.")

                pause()

                continue

            add_operation_alias(
                operation_name,
                alias,
            )

            print("\nAlias added successfully.")

            pause()

        elif choice == "2":

            aliases = list_operation_aliases()

            print()

            if not aliases:

                print("No aliases found.")

                pause()

                continue

            print(
                f"{'ID':<4}"
                f"{'ALIAS':<20}"
                f"{'OPERATION':<25}"
            )

            print("-" * 49)

            for alias in aliases:

                print(
                    f"{alias['id']:<4}"
                    f"{alias['alias']:<20}"
                    f"{alias['operation_name']:<25}"
                )

            pause()


        elif choice == "3":

            alias = input(
                "Alias : "
            ).strip()

            alias_data = get_operation_alias(
                alias
            )

            if alias_data is None:

                print("\nAlias not found.")

                pause()

                continue

            print()

            print(
                f"Alias     : {alias_data['alias']}"
            )

            print(
                f"Operation : {alias_data['operation_name']}"
            )

            confirm = input(
                "\nDelete this alias? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nDeletion cancelled.")

                pause()

                continue

            delete_operation_alias(
                alias
            )

            print("\nAlias deleted successfully.")

            pause()
            
        elif choice == "0":

            break

        else:

            print("\nInvalid choice.")

            pause()

def style_operation_rates_menu():

    while True:

        clear_screen()

        print("=" * 60)
        print("STYLE OPERATION RATES".center(60))
        print("=" * 60)

        print("\n1. Add Rate")
        print("2. List Rates")
        print("3. Search Style Rates")
        print("4. Update Rate")
        print("5. Delete Rate")
        print("0. Back")

        choice = input("\nChoice : ").strip()

        if choice == "1":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_exists(style_no):

                print("\nStyle not found.")

                pause()

                continue

            operation_name = input(
                "Operation : "
            ).strip()

            if not operation_exists(operation_name):

                print("\nOperation not found.")

                pause()

                continue

            try:

                rate = float(
                    input(
                    "Rate : "
                )
            )

            except ValueError:

                print("\nInvalid rate.")

                pause()

                continue

            confirm = input(
                "\nSave Rate? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nOperation cancelled.")

                pause()

                continue

            add_style_operation_rate(
                style_no=style_no,
                operation_name=operation_name,
                rate=rate,
            )

            print("\nRate added successfully.")

            pause()

        elif choice == "2":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_exists(style_no):

                print("\nStyle not found.")

                pause()

                continue

            rates = get_style_operation_rates(
                style_no
            )

            print()

            if not rates:

                print("No rates configured for this style.")

                pause()

                continue

            print(
                f"{'OPERATION':<30}"
                f"{'RATE':>10}"
            )

            print("-" * 40)

            for row in rates:

                print(
                    f"{row['operation']:<30}"
                    f"{row['rate']:>10.2f}"
                )

            pause()

        elif choice == "3":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_exists(style_no):

                print("\nStyle not found.")

                pause()

                continue

            rates = get_style_operation_rates(
                style_no
            )

            print()

            if not rates:

                print("No rates found for this style.")

                pause()

                continue

            print(
                f"Rates for Style : {style_no.upper()}"
            )

            print()

            print(
                f"{'OPERATION':<30}"
                f"{'RATE':>10}"
            )

            print("-" * 40)

            for row in rates:

                print(
                    f"{row['operation']:<30}"
                    f"{row['rate']:>10.2f}"
                )

            pause()

        elif choice == "4":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_exists(style_no):

                print("\nStyle not found.")

                pause()

                continue

            operation_name = input(
                "Operation : "
            ).strip()

            if not operation_exists(operation_name):

                print("\nOperation not found.")

                pause()

                continue

            try:

                new_rate = float(
                    input(
                        "New Rate : "
                    )
                )

            except ValueError:

                print("\nInvalid rate.")

                pause()

                continue

            confirm = input(
                "\nUpdate this rate? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nUpdate cancelled.")

                pause()

                continue

            update_style_operation_rate(
                style_no=style_no,
                operation_name=operation_name,
                new_rate=new_rate,
            )

            print("\nRate updated successfully.")

            pause()

        elif choice == "5":

            style_no = input(
                "Style Number : "
            ).strip()

            if not style_exists(style_no):

                print("\nStyle not found.")

                pause()

                continue

            operation_name = input(
                "Operation : "
            ).strip()

            if not operation_exists(operation_name):

                print("\nOperation not found.")

                pause()

                continue

            confirm = input(
                "\nDelete this rate? (Y/N): "
            ).strip().upper()

            if confirm != "Y":

                print("\nDeletion cancelled.")

                pause()

                continue

            delete_style_operation_rate(
                style_no=style_no,
                operation_name=operation_name,
            )

            print("\nRate deleted successfully.")

            pause()

        elif choice == "0":

            break

        else:

            print("\nInvalid choice.")

            pause()


# ==========================================================
# MAIN
# ==========================================================

def main():

    while True:

        choice = main_menu()

        if choice == "1":

            departments_menu()

        elif choice == "2":

            contractors_menu()

        elif choice == "3":

            employees_menu()

        elif choice == "4":

            styles_menu()

        elif choice == "5":

            operations_menu()

        elif choice == "6":

            style_operation_rates_menu()


        elif choice == "0":

            print("\nGoodbye!")

            break

        else:

            print("\nModule not implemented yet.")

            pause()


if __name__ == "__main__":

    main()