from collections.abc import Generator
import sqlite3

from database import connect_database


def get_db() -> Generator[sqlite3.Connection, None, None]:

    connection = connect_database()

    try:
        yield connection
    finally:
        connection.close()