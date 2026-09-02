from database import connect_database

def get_or_create_contractor(connection,contractor_name):

    cursor = connection.cursor()

    contractor_name = contractor_name.strip().upper()

    cursor.execute(
        """
        SELECT id
        FROM contractors
        WHERE name = ?
        """,
        (contractor_name,)
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]
    
    commission_rate = get_valid_commission_rate()

    cursor.execute(
        """
        INSERT INTO contractors(name, commission_rate)
        VALUES(?,?)
        """,
        (
            contractor_name,
            commission_rate,
        )
    )

    return cursor.lastrowid

def get_department_id(connection, department_name):

    cursor = connection.cursor()

    department_name = department_name.strip().upper()

    cursor.execute(
        """
        SELECT id
        FROM departments
        WHERE name = ?
        """,
        (department_name,)
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    raise LookupError(f"Department '{department_name}' not found.")

def employee_exists(connection, name):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE name = ?
        """,
        (name,)
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]

def update_employee(
        connection,
        employee_id,
        employee_code,
        department_id,
        pay_type,
        contractor_id,
        shift_rate,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET
            employee_code = ?,
            department_id = ?,
            pay_type = ?,
            contractor_id = ?,
            shift_rate = ?
        WHERE id = ?
        """,
        (
            employee_code,
            department_id,
            pay_type,
            contractor_id,
            shift_rate,
            employee_id,
        )
    )

def deactivate_employee(connection, employee_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET status = 'inactive'
        WHERE id = ?
        """,
        (employee_id,)
    )

def get_valid_employee_name():

    while True:

        name = input("Employee Name: ").strip().upper()

        if name == "":
            print("Employee name cannot be empty.")
            continue

        return name

def get_employee_code():

    return input("Employee Code (Optional): ").strip().upper()

def get_valid_pay_type():

    while True:

        pay_type = input("Pay Type (PIECE/SHIFT): ").strip().upper()

        if pay_type in ("PIECE", "SHIFT"):
            return pay_type

        print("Invalid pay type.")

def get_valid_shift_rate():

    while True:

        try:

            rate = float(input("Shift Rate: "))

            if rate <= 0:
                print("Shift rate must be greater than 0.")
                continue

            return rate

        except ValueError:
            print("Invalid shift rate.")

def get_valid_commission_rate():

    while True:

        try:

            rate = float(input("Commission Rate (%): "))

            if rate < 0:
                print("Commission cannot be negative.")
                continue

            return rate

        except ValueError:
            print("Invalid commission rate.")

def add_employee():

    connection = connect_database()

    try:

        cursor = connection.cursor()

        name = get_valid_employee_name()

        employee_id = employee_exists(
            connection,
            name,
        )

        department_name = input("Department: ").strip().upper()

        department_id = get_department_id(connection, department_name)

        pay_type = get_valid_pay_type()

        employee_code = get_employee_code()

        if pay_type == "PIECE":

            shift_rate = None
            contractor_id = None

        elif pay_type == "SHIFT":

            shift_rate = get_valid_shift_rate()

            contractor_name = input("Contractor Name (leave blank if none): ").strip()

            if contractor_name == "":
                contractor_id = None
            else:
                contractor_id = get_or_create_contractor(connection, contractor_name)

        else:

            print("Invalid pay type.")
            return

        if employee_id is not None:

            print()
            print("Employee already exists.")
            print("1. Update")
            print("2. Deactivate")
            print("3. Skip")

            option = input("Choice: ").strip()

            while option not in ("1", "2", "3"):
                option = input("Choose 1, 2 or 3: ").strip()

            if option == "1":

                update_employee(
                    connection,
                    employee_id,
                    employee_code,
                    department_id,
                    pay_type,
                    contractor_id,
                    shift_rate,
                )

                return

            elif option == "2":

                deactivate_employee(
                    connection,
                    employee_id,
                )

                return

            elif option == "3":
                return

        cursor.execute(
            """
            INSERT INTO employees(
                employee_code,
                name,
                pay_type,
                department_id,
                contractor_id,
                shift_rate
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                employee_code,
                name,
                pay_type,
                department_id,
                contractor_id,
                shift_rate,
            )
        )

        connection.commit()

    except Exception as error:

        print(f"Failed to add employee: {error}")

    finally:

        connection.close()

if __name__ == "__main__":
    add_employee()