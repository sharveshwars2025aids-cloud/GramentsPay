from database import connect_database


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


def get_valid_week_id():

    while True:

        try:
            return int(input("Week ID: "))

        except ValueError:
            print("Invalid Week ID.")


def get_valid_category():

    while True:

        category = input("Expense Name: ").strip().upper()

        if category == "":
            print("Expense name cannot be empty.")
            continue

        return category


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


def insert_expense(
        connection,
        week_id,
        category,
        amount,
        notes,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO expenses(
            week_id,
            category,
            amount,
            notes
        )
        VALUES(?,?,?,?)
        """,
        (
            week_id,
            category,
            amount,
            notes,
        )
    )


def expense_exists(
        connection,
        week_id,
        category,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM expenses
        WHERE
            week_id = ?
            AND category = ?
        """,
        (
            week_id,
            category,
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]


def update_expense(
        connection,
        expense_id,
        amount,
        notes,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE expenses
        SET
            amount = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            amount,
            notes,
            expense_id,
        )
    )


def delete_expense(
        connection,
        expense_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM expenses
        WHERE id = ?
        """,
        (expense_id,)
    )


def add_expense():

    connection = connect_database()

    try:

        week_id = get_valid_week_id()

        if not week_exists(connection, week_id):
            print("Week not found.")
            return

        while True:

            category = get_valid_category()

            amount = get_valid_amount()

            notes = input("Notes (Optional): ").strip()

            expense_id = expense_exists(
                connection,
                week_id,
                category,
            )

            if expense_id is not None:

                print()
                print("Expense already exists.")
                print("1. Update")
                print("2. Delete")
                print("3. Skip")

                option = input("Choice: ").strip()

                while option not in ("1", "2", "3"):
                    option = input("Choose 1, 2 or 3: ").strip()

                if option == "1":

                    update_expense(
                        connection,
                        expense_id,
                        amount,
                        notes,
                    )

                    connection.commit()
                    continue

                elif option == "2":

                    delete_expense(
                        connection,
                        expense_id,
                    )

                    connection.commit()
                    continue

                elif option == "3":
                    continue

            insert_expense(
                connection,
                week_id,
                category,
                amount,
                notes,
            )

            choice = input("Add another expense? (Y/N): ").strip().upper()

            while choice not in ("Y", "N"):
                choice = input("Please enter Y or N: ").strip().upper()

            if choice == "N":
                break

        connection.commit()

    except Exception as error:

        print(f"Failed to add expense: {error}")

    finally:

        connection.close()


if __name__ == "__main__":
    add_expense()