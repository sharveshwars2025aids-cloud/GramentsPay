from database import connect_database
from attendance_checker import check_attendance_vs_shift


connection = connect_database()

try:

    week_id = 2

    mismatches = check_attendance_vs_shift(
        connection,
        week_id,
    )

    print("=" * 60)
    print("ATTENDANCE MISMATCH CHECK")
    print("=" * 60)

    if not mismatches:

        print("No attendance mismatches found.")

    else:

        print(f"Found {len(mismatches)} mismatch(es):")
        print()

        for mismatch in mismatches:

            print("-" * 60)
            print(
                f"Employee : {mismatch['employee_code']} "
                f"- {mismatch['employee_name']}"
            )
            print(f"Date     : {mismatch['work_date']}")
            print(f"Shifts   : {mismatch['recorded_shifts']}")
            print(
                f"Attendance: {mismatch['attendance_status']}"
            )
            print(
                f"Source   : {mismatch['attendance_source']}"
            )
            print(f"Reason   : {mismatch['reason']}")

finally:

    connection.close()