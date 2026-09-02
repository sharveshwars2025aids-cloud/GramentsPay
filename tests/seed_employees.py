from database import connect_database

employees = [
    "B.LAKSHMI",
    "CHANDRASEKAR",
    "JAYAMANI",
    "KALIAPPAN",
    "LOGANAYAKI",
    "MAHESWARI",
    "MANOHAR",
    "SELVARAJ",
    "SELVARANI",
    "SENTHIL KUMAR",
    "UMA",
]

connection = connect_database()
cursor = connection.cursor()

for employee in employees:
    cursor.execute(
        """
        INSERT INTO employees(name)
        VALUES(?)
        """,
        (employee,)
    )
    
connection.commit()
connection.close()

print("Employees added successfully.")