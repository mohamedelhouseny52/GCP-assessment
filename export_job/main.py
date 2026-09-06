import csv
import os
from datetime import datetime

from MySql.MySql import get_connection


COLUMNS = [
    "customer_id",
    "total_events",
    "total_value",
    "purchase_count",
    "view_count",
    "cart_count",
    "days_since_last_event",
    "label_high_value",
]


def get_customer_aggregates():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            customer_id,
            COUNT(*) AS total_events,

            SUM(
                CASE
                    WHEN event_type = 'purchase'
                    THEN COALESCE(value, 0)
                    ELSE 0
                END
            ) AS total_value,

            SUM(event_type = 'purchase') AS purchase_count,
            SUM(event_type = 'view') AS view_count,
            SUM(event_type = 'add_to_cart') AS cart_count,

            MAX(event_timestamp) AS last_event_at

        FROM events

        GROUP BY customer_id
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def prepare_training_rows(rows, now=None):
    if now is None:
        now = datetime.now()

    training_rows = []

    for row in rows:
        last_event_at = row["last_event_at"]

        days_since_last_event = (
            now - last_event_at
        ).days

        total_value = float(row["total_value"] or 0)

        label_high_value = 1 if total_value > 200 else 0

        training_rows.append({
            "customer_id": row["customer_id"],
            "total_events": int(row["total_events"]),
            "total_value": total_value,
            "purchase_count": int(row["purchase_count"]),
            "view_count": int(row["view_count"]),
            "cart_count": int(row["cart_count"]),
            "days_since_last_event": days_since_last_event,
            "label_high_value": label_high_value,
        })

    return training_rows


def write_csv(training_rows, output_path="training_data.csv"):
    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=COLUMNS
        )

        writer.writeheader()
        writer.writerows(training_rows)


def export_training_data(output_path="training_data.csv"):
    rows = get_customer_aggregates()

    training_rows = prepare_training_rows(rows)

    write_csv(
        training_rows,
        output_path
    )

    print(
        f"Training data exported to {output_path}"
    )

    print(
        f"Customers exported: {len(training_rows)}"
    )

    return training_rows


if __name__ == "__main__":
    output_path = os.getenv(
        "OUTPUT_PATH",
        "training_data.csv"
    )

    export_training_data(output_path)