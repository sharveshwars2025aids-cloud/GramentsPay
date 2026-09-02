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


def get_valid_text(prompt, required=True):

    while True:

        value = input(prompt).strip().upper()

        if required and value == "":
            print("This field cannot be empty.")
            continue

        return value


def get_valid_number(prompt, allow_zero=True):

    while True:

        try:

            value = float(input(prompt))

            if not allow_zero and value <= 0:
                print("Value must be greater than 0.")
                continue

            return value

        except ValueError:

            print("Invalid number.")


def insert_outsource_payment(
        connection,
        week_id,
        style,
        item,
        qty,
        rate,
        amount,
        centre_name="",
        remarks="",
):

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO outsource_payments(
            week_id,
            style,
            item,
            qty,
            rate,
            amount,
            centre_name,
            remarks
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            week_id,
            style,
            item,
            qty,
            rate,
            amount,
            centre_name,
            remarks,
        )
    )

    return cursor.lastrowid


def delete_outsource_payment(
        connection,
        outsource_payment_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE
        FROM outsource_payments
        WHERE id = ?
        """,
        (outsource_payment_id,)
    )


def add_outsource_payments():

    connection = connect_database()

    try:

        week_id = get_valid_week_id()

        if not week_exists(connection, week_id):
            print("Week not found.")
            return

        went_out = input(
            "Did any products/work go to another factory? (Y/N): "
        ).strip().upper()

        while went_out not in ("Y", "N"):
            went_out = input("Please enter Y or N: ").strip().upper()

        if went_out == "N":
            print("No outsource payments recorded for this week.")
            return

        while True:

            centre_name = get_valid_text("Work Centre: ")

            style = get_valid_text("Style: ")

            item = get_valid_text("Item: ")

            qty = get_valid_number("Qty: ", allow_zero=False)

            rate = get_valid_number("Rate: ", allow_zero=False)

            amount = qty * rate

            remarks = input("Remarks (Optional): ").strip()

            insert_outsource_payment(
                connection,
                week_id,
                style,
                item,
                qty,
                rate,
                amount,
                centre_name,
                remarks,
            )

            choice = input(
                "Add another outsource payment? (Y/N): "
            ).strip().upper()

            while choice not in ("Y", "N"):
                choice = input("Please enter Y or N: ").strip().upper()

            if choice == "N":
                break

        connection.commit()

    except Exception as error:

        print(f"Failed to add outsource payment: {error}")

    finally:

        connection.close()


if __name__ == "__main__":
    add_outsource_payments()