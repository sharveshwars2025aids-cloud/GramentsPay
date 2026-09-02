from database import connect_database


def main():

    connection = connect_database()

    try:
        cursor = connection.cursor()

        # Get one employee
        cursor.execute("""
            SELECT id, name
            FROM employees
            WHERE status = 'active'
            LIMIT 1
        """)

        employee = cursor.fetchone()

        if employee is None:
            print("No employee found.")
            return

        employee_id, employee_name = employee

        # Insert test attendance
        cursor.execute("""
            INSERT INTO attendance_records (
                employee_id,
                work_date,
                entry_time,
                exit_time,
                status,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            "2026-09-01",
            "2026-09-01 09:02:15",
            "2026-09-01 18:01:30",
            "PRESENT",
            "BIOMETRIC"
        ))

        connection.commit()

        print("Attendance inserted successfully.")
        print(f"Employee: {employee_name}")

        # Read it back
        cursor.execute("""
            SELECT
                e.name,
                a.work_date,
                a.entry_time,
                a.exit_time,
                a.status,
                a.source
            FROM attendance_records a
            JOIN employees e
                ON a.employee_id = e.id
            WHERE a.work_date = ?
        """, ("2026-09-01",))

        print("\nAttendance:")
        for row in cursor.fetchall():
            print(row)

    except Exception as error:
        connection.rollback()
        print("Failed:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    main()