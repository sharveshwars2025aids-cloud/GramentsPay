from utils.text import normalize_name
from utils.validators import ensure_unique_name

def get_all_contractors(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            commission_amount,
            status
        FROM contractors
        ORDER BY name
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_contractor(connection, contractor_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            commission_amount,
            status
        FROM contractors
        WHERE id=?
        """,
        (contractor_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_contractor(connection, contractor):

    name = normalize_name(contractor.name)

    ensure_unique_name(
        connection,
        table="contractors",
        column="name",
        value=name,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO contractors(
            name,
            commission_amount
        )
        VALUES(?, ?)
        """,
        (
            contractor.name,
            contractor.commission_amount,
        ),
    )

    connection.commit()

    return get_contractor(
        connection,
        cursor.lastrowid,
    )


def update_contractor(
    connection,
    contractor_id,
    contractor,
):

    name = normalize_name(contractor.name)

    ensure_unique_name(
        connection,
        table="contractors",
        column="name",
        value=name,
        exclude_id=contractor_id,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contractors
        SET
            name=?,
            commission_amount=?,
            status=?
        WHERE id=?
        """,
        (
            contractor.name,
            contractor.commission_amount,
            contractor.status,
            contractor_id,
        ),
    )

    connection.commit()

    return get_contractor(
        connection,
        contractor_id,
    )


def delete_contractor(
    connection,
    contractor_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE contractors
        SET status='inactive'
        WHERE id=?
        """,
        (contractor_id,),
    )

    connection.commit()