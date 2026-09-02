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


def bonus_exists(connection, week_id, employee_id, bonus_type):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM bonuses
        WHERE
            week_id = ?
            AND employee_id = ?
            AND bonus_type = ?
        """,
        (
            week_id,
            employee_id,
            bonus_type,
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]

def get_valid_bonus_type():

    while True:

        bonus_type = input("Bonus Type: ").strip().upper()

        if bonus_type == "":
            print("Bonus Type cannot be empty.")
            continue

        return bonus_type


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

def insert_bonus(
        connection,
        week_id,
        employee_id,
        bonus_type,
        amount,
        notes,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO bonuses(
            week_id,
            employee_id,
            bonus_type,
            amount,
            notes
        )
        VALUES(?,?,?,?,?)
        """,
        (
            week_id,
            employee_id,
            bonus_type,
            amount,
            notes,
        )
    )

def update_bonus(
        connection,
        bonus_id,
        amount,
        notes,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE bonuses
        SET
            amount = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            amount,
            notes,
            bonus_id,
        )
    )

def delete_bonus(connection, bonus_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM bonuses
        WHERE id = ?
        """,
        (bonus_id,)
    )

def add_bonus():

    connection = connect_database()

    try:

        employees = get_active_employees(connection)

        if not employees:
            print("No active employees found.")
            return

        week_id = int(input("Week ID: "))

        if not week_exists(connection, week_id):
            print("Week not found.")
            return

        for employee_id, employee_name in employees:

            print("-" * 40)
            print(f"Employee: {employee_name}")

            choice = input("Any bonus(Y/N): ").strip().upper()

            while choice not in ("Y" , "N"):
                choice = input("Please enter Y or N: ").strip().upper()

            if choice == "N":
                continue

            bonus_type = get_valid_bonus_type()

            amount = get_valid_amount()

            notes = input("Notes (Optional): ").strip()

            bonus_id = bonus_exists(
                connection,
                week_id,
                employee_id,
                bonus_type,
            )

            if bonus_id is not None:

                print()

                print("Bonus already exists.")

                print("1. Update")

                print("2. Delete")

                print("3. Skip")

                option = input("Choice: ").strip()

                while option not in ("1", "2", "3"):

                    option = input("Choose 1, 2 or 3: ").strip()

                if option == "1":

                    update_bonus(
                        connection,
                        bonus_id,
                        amount,
                        notes,
                )

                elif option == "2":

                    delete_bonus(
                        connection,
                        bonus_id,
                    )

                continue

            insert_bonus(
                connection,
                week_id,
                employee_id,
                bonus_type,
                amount,
                notes,
            )

        connection.commit()

    except Exception as error:

        print(f"Failed to add bonus: {error}")

    finally:

        connection.close()

if __name__ == "__main__":
    add_bonus()