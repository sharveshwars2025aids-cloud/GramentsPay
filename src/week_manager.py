from database import connect_database
from datetime import datetime

def get_valid_date(prompt):

    while True:

        date_text = input(prompt).strip()

        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            return date_text

        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")

def week_exists(connection, week_start, week_end):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM weeks
        WHERE week_start = ?
        AND week_end = ?
        """,
        (
            week_start,
            week_end,
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]

def create_week(connection, week_start, week_end):

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO weeks(
                week_start,
                week_end
            )
            VALUES(?,?)
            """,
            (
                week_start,
                week_end,
            )
       )

        return cursor.lastrowid

def add_week():

    connection = connect_database()

    try:

        week_start = get_valid_date("Week Start (YYYY-MM-DD): ")
        week_end = get_valid_date("Week End (YYYY-MM-DD): ")

        start = datetime.strptime(week_start, "%Y-%m-%d")
        end = datetime.strptime(week_end, "%Y-%m-%d")

        if end < start:
            print("Week end cannot be before week start.")
            return

        week_id = week_exists(
            connection,
            week_start,
            week_end,
        )

        if week_id is None:

            week_id = create_week(
                connection,
                week_start,
                week_end,
            )

            connection.commit()

        print(f"Week ID: {week_id}")

    except Exception as error:

        print(f"Failed to create week: {error}")

    finally:

        connection.close()
if __name__ == "__main__":
    add_week()
