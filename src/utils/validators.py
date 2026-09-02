import sqlite3
from core.exceptions import DuplicateRecordError

def ensure_unique_name(
    connection: sqlite3.Connection,
    *,
    table: str,
    column: str,
    value: str,
    exclude_id: int | None = None,
):
    """
    Raises ValueError if a record with the same
    name already exists (case-insensitive).
    """

    cursor = connection.cursor()

    sql = f"""
    SELECT id
    FROM {table}
    WHERE UPPER({column}) = UPPER(?)
    """

    parameters = [value]

    if exclude_id is not None:
        sql += " AND id <> ?"
        parameters.append(exclude_id)

    cursor.execute(sql, tuple(parameters))

    if cursor.fetchone():

        raise DuplicateRecordError(
            f"{table[:-1].capitalize()} '{value}' already exists."
        )