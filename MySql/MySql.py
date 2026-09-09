"""Small MySQL helper used by the event writer and export job."""

import os
from datetime import datetime

import mysql.connector


def get_connection():
    """Connect using environment variables, with local defaults."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "event_db"),
    )


def insert_event(event_data):
    """Insert one validated event into MySQL."""
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO events
            (customer_id, event_type, product_id, value, event_timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    event_timestamp = datetime.fromisoformat(
        event_data["timestamp"].replace("Z", "+00:00")
    )
    values = (
        event_data["customer_id"],
        event_data["event_type"],
        event_data["product_id"],
        event_data.get("value"),
        event_timestamp,
    )

    try:
        cursor.execute(query, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
