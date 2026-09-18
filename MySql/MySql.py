"""Shared MySQL connection and event-insertion helpers."""

import os
from datetime import datetime, timezone
from functools import lru_cache

from mysql.connector.pooling import MySQLConnectionPool


@lru_cache(maxsize=1)
def get_pool():
    return MySQLConnectionPool(
        pool_name="event_pipeline",
        pool_size=5,
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "event_db"),
    )


def get_connection():
    """Borrow a connection; close() returns it to the pool."""
    return get_pool().get_connection()


def insert_event(event_data):
    """Insert one validated event into MySQL."""
    query = """
        INSERT INTO events
            (customer_id, event_type, product_id, value, event_timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    parsed_timestamp = datetime.fromisoformat(
        event_data["timestamp"].replace("Z", "+00:00")
    )
    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)
    event_timestamp = parsed_timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    values = (
        event_data["customer_id"],
        event_data["event_type"],
        event_data["product_id"],
        event_data.get("value"),
        event_timestamp,
    )

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
