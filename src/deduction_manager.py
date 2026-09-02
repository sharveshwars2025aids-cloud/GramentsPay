from database import connect_database

def get_active_employees(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 
            id,
            name
        FROM employees
        WHERE status = 'active'
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

def deduction_exists(
        connection,
        week_id,
        employee_id,
        deduction_type,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM deductions
        WHERE
            week_id = ?
            AND employee_id = ?
            AND deduction_type = ?
        """,
        (
            week_id,
            employee_id,
            deduction_type,
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]

def get_valid_deduction_type():

    while True:

        deduction_type = input("Deduction Type: ").strip().upper()

        if deduction_type == "":
            print("Deduction Type cannot be empty.")
            continue

        return deduction_type

def get_valid_amount():

    while True:

        try:

            amount = float(input("Amount: "))

            if amount <= 0:
                print("Amount must be greater than 0.")
                continue

            return amount

        except ValueError:

            print("Invalid amount.")

def insert_deduction(
        connection,
        week_id,
        employee_id,
        deduction_type,
        amount,
        notes,
):
    
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO deductions(
            week_id,
            employee_id,
            deduction_type,
            amount,
            notes
        )
        VALUES(?,?,?,?,?)
        """,
        (
            week_id,
            employee_id,
            deduction_type,
            amount,
            notes,
        )
    )

def update_deduction(
        connection,
        deduction_id,
        amount,
        notes,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE deductions
        SET
            amount = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            amount,
            notes,
            deduction_id,
        )
    )

def delete_deduction(connection, deduction_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM deductions
        WHERE id = ?
        """,
        (deduction_id,)
    )
    
def get_valid_week_id():

    while True:

        try:
            return int(input("Week ID: "))

        except ValueError:
            print("Invalid Week ID.")

def add_deduction():

    connection = connect_database()

    try:

        employees = get_active_employees(connection)

        if not employees:
            print("No active employees found.")
            return

        week_id = get_valid_week_id()

        if not week_exists(connection, week_id):
            print("Week not found.")
            return


        for employee_id, employee_name in employees:

            print("-" * 40)
            print(f"Employee : {employee_name}")

            choice = input("Any deduction? (Y/N): ").strip().upper()

            while choice not in ("Y" , "N"):
                choice = input("Please enter Y or N: ").strip().upper()

            if choice == "N":
                continue

            deduction_type = get_valid_deduction_type()

            amount = get_valid_amount()

            notes = input("Notes (Optional): ").strip()

            deduction_id = deduction_exists(
                connection,
                week_id,
                employee_id,
                deduction_type,
            )

            if deduction_id is not None:

                print()
                print("Deduction already exists.")
                print("1. Update")
                print("2. Delete")
                print("3. Skip")

                option = input("Choice: ").strip()

                while option not in ("1", "2", "3"):
                    option = input("Choose 1, 2 or 3: ").strip()

                if option == "1":

                    update_deduction(
                        connection,
                        deduction_id,
                        amount,
                        notes,
                    )

                    continue

                elif option == "2":

                    delete_deduction(
                        connection,
                        deduction_id,
                    )

                    continue

                elif option == "3":
                    continue
                    
            insert_deduction(
                connection,
                week_id,
                employee_id,
                deduction_type,
                amount,
                notes,
            )

        connection.commit()



    except Exception as error:

        print(f"Failed to add deduction: {error}")

    finally:

        connection.close()

if __name__ == "__main__":
    add_deduction()