from utils.text import normalize_name
from utils.validators import ensure_unique_name

def get_all_departments(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            status
        FROM departments
        ORDER BY name
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_department(connection, department_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            status
        FROM departments
        WHERE id=?
        """,
        (department_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_department(connection, department):

    name = normalize_name(department.name)

    ensure_unique_name(
        connection,
        table="departments",
        column="name",
        value=name,
    )



    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO departments(name)
        VALUES(?)
        """,
        (department.name,),
    )

    connection.commit()

    return get_department(
        connection,
        cursor.lastrowid,
    )


def update_department(
    connection,
    department_id,
    department,
):

    name = normalize_name(department.name)

    ensure_unique_name(
        connection,
        table="departments",
        column="name",
        value=name,
        exclude_id=department_id,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE departments
        SET
            name=?,
            status=?
        WHERE id=?
        """,
        (
            department.name,
            department.status,
            department_id,
        ),
    )

    connection.commit()

    return get_department(
        connection,
        department_id,
    )


def delete_department(
    connection,
    department_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE departments
        SET status='inactive'
        WHERE id=?
        """,
        (department_id,),
    )

    connection.commit()