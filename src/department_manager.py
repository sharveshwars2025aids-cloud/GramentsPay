from database import connect_database


def department_exists(
        connection,
        department_name,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM departments
        WHERE name = ?
        """,
        (department_name,)
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]


def insert_department(
        connection,
        department_name,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO departments(name)
        VALUES(?)
        """,
        (department_name,)
    )


def update_department(
        connection,
        department_id,
        department_name,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE departments
        SET name = ?
        WHERE id = ?
        """,
        (
            department_name,
            department_id,
        )
    )


def deactivate_department(
        connection,
        department_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE departments
        SET status = 'inactive'
        WHERE id = ?
        """,
        (department_id,)
    )


def get_valid_department_name():

    while True:

        department_name = input(
            "Department Name: "
        ).strip().upper()

        if department_name == "":

            print("Department name cannot be empty.")
            continue

        return department_name


def add_department():

    connection = connect_database()

    try:

        department_name = get_valid_department_name()

        department_id = department_exists(
            connection,
            department_name,
        )

        if department_id is not None:

            print()
            print("Department already exists.")
            print("1. Update")
            print("2. Deactivate")
            print("3. Skip")

            option = input("Choice: ").strip()

            while option not in ("1", "2", "3"):

                option = input(
                    "Choose 1, 2 or 3: "
                ).strip()

            if option == "1":

                update_department(
                    connection,
                    department_id,
                    department_name,
                )

                connection.commit()

                print("Department updated successfully.")

                return

            elif option == "2":

                deactivate_department(
                    connection,
                    department_id,
                )

                connection.commit()

                print("Department deactivated successfully.")

                return

            else:

                print("Skipped.")

                return

        insert_department(
            connection,
            department_name,
        )

        connection.commit()

        print("Department added successfully.")

    except Exception as error:

        print(f"Failed to add department: {error}")

    finally:

        connection.close()


if __name__ == "__main__":

    add_department()