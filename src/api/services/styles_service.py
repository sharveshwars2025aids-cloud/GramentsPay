from utils.text import normalize_name
from utils.validators import ensure_unique_name


def get_all_styles(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            style_no,
            style_name,
            status
        FROM styles
        ORDER BY style_no
        """
    )

    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_style(connection, style_id):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            style_no,
            style_name,
            status
        FROM styles
        WHERE id=? OR UPPER(style_no)=?
        """,
        (style_id, str(style_id).strip().upper()),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    columns = [column[0] for column in cursor.description]

    return dict(zip(columns, row))


def create_style(connection, style):
    from fastapi import HTTPException

    style_no = normalize_name(style.style_no)
    if not style_no:
        raise HTTPException(status_code=400, detail="Style number is required.")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM styles WHERE LOWER(TRIM(style_no)) = LOWER(?)",
        (style_no,),
    )
    if cursor.fetchone():
        raise HTTPException(
            status_code=409,
            detail=f"Style number '{style_no}' already exists.",
        )

    try:
        cursor.execute(
            """
            INSERT INTO styles (style_no, style_name)
            VALUES (?, ?)
            """,
            (style_no, style.style_name),
        )
        connection.commit()
        last_id = cursor.lastrowid
    except HTTPException:
        connection.rollback()
        raise
    except Exception as exc:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return get_style(connection, last_id)



def update_style(
    connection,
    style_id,
    style,
):

    existing = get_style(connection, style_id)
    if existing is None:
        return None

    actual_id = existing["id"]
    style_no = normalize_name(style.style_no)

    ensure_unique_name(
        connection,
        table="styles",
        column="style_no",
        value=style_no,
        exclude_id=actual_id,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE styles
        SET
            style_no=?,
            style_name=?,
            status=?
        WHERE id=?
        """,
        (
            style_no,
            style.style_name,
            style.status,
            actual_id,
        ),
    )

    connection.commit()

    return get_style(
        connection,
        actual_id,
    )


def delete_style(
    connection,
    style_id,
):

    existing = get_style(connection, style_id)
    if existing is None:
        return

    actual_id = existing["id"]

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE styles
        SET status='inactive'
        WHERE id=?
        """,
        (actual_id,),
    )

    connection.commit()