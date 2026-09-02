from utils.text import normalize_name
from utils.validators import ensure_unique_name

def get_all_operations(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            operation_name,
            status
        FROM operations
        ORDER BY operation_name
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_operation(connection, operation_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            operation_name,
            status
        FROM operations
        WHERE id=?
        """,
        (operation_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_operation(connection, operation):
    from fastapi import HTTPException

    name = normalize_name(operation.operation_name)
    if not name:
        raise HTTPException(status_code=400, detail="Operation name is required.")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM operations WHERE LOWER(TRIM(operation_name)) = LOWER(?)",
        (name,),
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=409,
            detail=f"Operation '{name}' already exists.",
        )

    try:
        cursor.execute(
            """
            INSERT INTO operations (operation_name)
            VALUES (?)
            """,
            (name,),
        )
        connection.commit()
        last_id = cursor.lastrowid
    except HTTPException:
        connection.rollback()
        raise
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return get_operation(connection, last_id)



def update_operation(
    connection,
    operation_id,
    operation,
):

    name = normalize_name(operation.operation_name)

    ensure_unique_name(
        connection,
        table="operations",
        column="operation_name",
        value=name,
        exclude_id=operation_id,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE operations
        SET
            operation_name=?,
            status=?
        WHERE id=?
        """,
        (
            operation.operation_name,
            operation.status,
            operation_id,
        ),
    )

    connection.commit()

    return get_operation(
        connection,
        operation_id,
    )


def delete_operation(
    connection,
    operation_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE operations
        SET status='inactive'
        WHERE id=?
        """,
        (operation_id,),
    )

    connection.commit()