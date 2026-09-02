from utils.text import normalize_alias
from utils.validators import ensure_unique_name

from core.exceptions import RecordNotFoundError

def get_all_operation_aliases(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            oa.id,
            oa.operation_id,
            o.operation_name,
            oa.alias,
            oa.status
        FROM operation_aliases oa
        JOIN operations o
            ON oa.operation_id = o.id
        ORDER BY oa.alias
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_operation_alias(
    connection,
    alias_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            oa.id,
            oa.operation_id,
            o.operation_name,
            oa.alias,
            oa.status
        FROM operation_aliases oa
        JOIN operations o
            ON oa.operation_id = o.id
        WHERE oa.id=?
        """,
        (alias_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_operation_alias(
    connection,
    operation_alias,
):

    alias = normalize_alias(
        operation_alias.alias
    )

    ensure_unique_name(
        connection,
        table="operation_aliases",
        column="alias",
        value=alias,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM operations
        WHERE id=?
          AND status='active'
        """,
        (operation_alias.operation_id,),
    )

    if cursor.fetchone() is None:

        raise RecordNotFoundError(
            "Operation not found."
        )

    cursor.execute(
        """
        INSERT INTO operation_aliases(
            operation_id,
            alias
        )
        VALUES(?,?)
        """,
        (
            operation_alias.operation_id,
            alias,
        ),
    )

    connection.commit()

    return get_operation_alias(
        connection,
        cursor.lastrowid,
    )


def update_operation_alias(
    connection,
    alias_id,
    operation_alias,
):

    alias = normalize_alias(
        operation_alias.alias
    )

    ensure_unique_name(
        connection,
        table="operation_aliases",
        column="alias",
        value=alias,
        exclude_id=alias_id,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM operations
        WHERE id=?
          AND status='active'
        """,
        (operation_alias.operation_id,),
    )

    if cursor.fetchone() is None:

        raise RecordNotFoundError(
            "Operation not found."
        )

    cursor.execute(
        """
        UPDATE operation_aliases
        SET
            operation_id=?,
            alias=?,
            status=?
        WHERE id=?
        """,
        (
            operation_alias.operation_id,
            alias,
            operation_alias.status,
            alias_id,
        ),
    )

    connection.commit()

    return get_operation_alias(
        connection,
        alias_id,
    )


def delete_operation_alias(
    connection,
    alias_id,
):

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE operation_aliases
        SET status='inactive'
        WHERE id=?
        """,
        (alias_id,),
    )

    connection.commit()