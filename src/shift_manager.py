from database import connect_database

def get_shift_employees(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            shift_rate
        FROM employees
        WHERE pay_type = 'SHIFT'
        AND status = 'active'
        ORDER BY name
        """
    )
    

    result = cursor.fetchall()
    return result

def week_exists(connection, week_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM weeks
        WHERE id = ?
        """,
        (week_id,)
    )

    return cursor.fetchone() is not None

def get_operation_id(connection, operation):
    cursor = connection.cursor()

    operation = (
        str(operation)
        .strip()
        .upper()
    )

    cursor.execute(
        """
        SELECT o.id
        FROM operation_aliases oa
        JOIN operations o
            ON oa.operation_id = o.id
        WHERE UPPER(oa.alias) = ?
        """,
        (operation,),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    cursor.execute(
        """
        SELECT id
        FROM operations
        WHERE UPPER(operation_name) = ?
        """,
        (operation,),
    )

    result = cursor.fetchone()

    if result is not None:
        return result[0]

    raise LookupError(
        f"Unknown operation '{operation}'."
    )

def shift_record_exists(
        connection,
        week_id,
        employee_id,
        operation_id,
        item,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM shift_records
        WHERE
            week_id = ?
            AND employee_id = ?
            AND operation_id = ?
            AND item = ?
        """,
        (
            week_id,
            employee_id,
            operation_id,
            item,
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]


def get_valid_week_id():

    while True:

        try:
            return int(input("Week ID: "))

        except ValueError:
            print("Invalid Week ID.")

def get_valid_shifts():

    while True:

        try:

            shifts = float(input("Shifts Worked: "))

            if shifts < 0:
                print("Shifts cannot be negative.")
                continue

            return shifts

        except ValueError:
            print("Invalid shift value.")

def insert_shift_record(
        connection,
        week_id,
        work_date,
        employee_id,
        operation_id,
        item,
        shifts,
        rate_per_shift,
        style_id=None,
        type=None,
        color=None,
):
    
    cursor = connection.cursor()

    daily_salary = shifts * rate_per_shift

    cursor.execute(
        """
        INSERT INTO shift_records(
            week_id,
            work_date,
            employee_id,
            operation_id,
            style_id,
            type,
            color,
            item,
            shifts,
            shift_rate,
            daily_salary
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            week_id,
            work_date,
            employee_id,
            operation_id,
            style_id,
            type or "",
            color or "",
            item,
            shifts,
            rate_per_shift,
            daily_salary,
        )
    )

    return cursor.lastrowid

def update_shift_record(
        connection,
        shift_record_id,
        shifts,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE shift_records
        SET shifts = ?
        WHERE id = ?
        """,
        (
            shifts,
            shift_record_id,
        )
    )

def delete_shift_record(
        connection,
        shift_record_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM shift_records
        WHERE id = ?
        """,
        (shift_record_id,)
    )


def get_valid_text(prompt):
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print("Value cannot be empty.")


def get_operation_id_from_input(connection):
    while True:
        operation = input("Operation: ").strip()

        if not operation:
            print("Operation cannot be empty.")
            continue

        try:
            return get_operation_id(connection, operation)
        except LookupError as error:
            print(error)
            print("Enter an existing operation or alias.")


def add_shift_records():

    connection = connect_database()

    try:

        shift_employees = get_shift_employees(connection)

        if not shift_employees:
            print("No active shift employees found.")
            return

        week_id = get_valid_week_id()

        if not week_exists(connection, week_id):
            print("Week not found.")
            return

        for employee_id, employee_name, employee_shift_rate in shift_employees:

            print("-" * 50)
            print(f"Employee      : {employee_name}")
            print(f"Default Rate  : {employee_shift_rate}")

            # ------------------------------------------
            # OPERATION
            # ------------------------------------------

            operation_id = get_operation_id_from_input(
                connection
            )

            # ------------------------------------------
            # ITEM
            # ------------------------------------------

            item = get_valid_text(
                "Item: "
            )

            # ------------------------------------------
            # SHIFT
            # ------------------------------------------

            shifts = get_valid_shifts()

            # ------------------------------------------
            # RATE
            # ------------------------------------------

            rate_input = input(
                f"Rate per Shift [{employee_shift_rate}]: "
            ).strip()

            if rate_input == "":
                rate_per_shift = employee_shift_rate

            else:
                try:
                    rate_per_shift = float(rate_input)

                    if rate_per_shift < 0:
                        print("Rate cannot be negative.")
                        continue

                except ValueError:
                    print("Invalid rate.")
                    continue

            # ------------------------------------------
            # SALARY
            # ------------------------------------------

            daily_salary = shifts * rate_per_shift

            print(f"Calculated Salary: {daily_salary}")

            # ------------------------------------------
            # EXISTING RECORD
            # ------------------------------------------

            shift_record_id = shift_record_exists(
                connection,
                week_id,
                employee_id,
                operation_id,
                item,
            )
            
            if shift_record_id is not None:

                print()
                print("Shift record already exists.")
                print("1. Update")
                print("2. Delete")
                print("3. Skip")

                option = input("Choice: ").strip()

                while option not in ("1", "2", "3"):
                    option = input(
                        "Choose 1, 2 or 3: "
                    ).strip()

                if option == "1":

                    update_shift_record(
                        connection,
                        shift_record_id,
                        shifts,
                    )

                    connection.commit()
                    continue

                elif option == "2":

                    delete_shift_record(
                        connection,
                        shift_record_id,
                    )

                    connection.commit()
                    continue

                elif option == "3":
                    continue

            # ------------------------------------------
            # INSERT
            # ------------------------------------------

            insert_shift_record(
                connection,
                week_id,
                None,              # work_date for now
                employee_id,
                operation_id,
                item,
                shifts,
                rate_per_shift,
            )

        connection.commit()

    except Exception as error:

        connection.rollback()

        print(
            f"Failed to add shift records: {error}"
        )

    finally:

        connection.close()


if __name__ == "__main__":
    add_shift_records()