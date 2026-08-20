import os
import mysql.connector

from datetime import datetime


def get_connection():

    connection = mysql.connector.connect(

        host=os.getenv(
            "MYSQL_HOST",
            "localhost"
        ),

        port=int(
            os.getenv(
                "MYSQL_PORT",
                "3306"
            )
        ),

        user=os.getenv(
            "MYSQL_USER",
            "root"
        ),

        password=os.getenv(
            "MYSQL_PASSWORD",
            "root"
        ),

        database=os.getenv(
            "MYSQL_DATABASE",
            "event_db"
        )
    )

    return connection


def insert_event(event_data):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO events (
            customer_id,
            event_type,
            product_id,
            value,
            event_timestamp
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    # Convert ISO-8601 timestamp into a Python datetime
    # that MySQL can store correctly.
    event_timestamp = datetime.fromisoformat(
        event_data["timestamp"].replace(
            "Z",
            "+00:00"
        )
    )

    values = (
        event_data["customer_id"],
        event_data["event_type"],
        event_data["product_id"],
        event_data.get("value"),
        event_timestamp
    )

    try:
        cursor.execute(
            query,
            values
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        raise error

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":

    connection = get_connection()

    print("Connected to MySQL")

    connection.close()


    test_event = {
        "customer_id": "cust_123",
        "event_type": "purchase",
        "product_id": "prod_456",
        "value": 44.99,
        "timestamp": "2026-08-20T13:20:00Z"
    }

    insert_event(test_event)

    print("Event inserted successfully")