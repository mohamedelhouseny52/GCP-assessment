from MySql.MySql import get_connection
from datetime import datetime, timezone
from google.cloud import firestore


def get_events():
    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            customer_id,
            event_type,
            value,
            event_timestamp
        FROM events
    """)

    events = cursor.fetchall()

    cursor.close()
    connection.close()

    return events


def aggregate_events(events):
    summaries = {}

    for event in events:
        customer_id = event["customer_id"]

        if customer_id not in summaries:
            summaries[customer_id] = {
                "customer_id": customer_id,
                "total_events": 0,
                "total_value": 0,
                "purchase_count": 0,
                "last_event_at": None
            }

        summaries[customer_id]["total_events"] += 1

        if event["event_type"] == "purchase":
            summaries[customer_id]["purchase_count"] += 1
            summaries[customer_id]["total_value"] += float(event["value"])

        event_time = event["event_timestamp"]

        if summaries[customer_id]["last_event_at"] is None:
            summaries[customer_id]["last_event_at"] = event_time

        elif event_time > summaries[customer_id]["last_event_at"]:
            summaries[customer_id]["last_event_at"] = event_time


    updated_at = datetime.now(timezone.utc)

    for customer_id in summaries:
        summaries[customer_id]["updated_at"] = updated_at

    return summaries


def aggregate_customer_stats(event, context):
    events = get_events()

    summaries = aggregate_events(events)

    for customer_id, summary in summaries.items():
        save_summary_to_firestore(customer_id, summary)

    print(summaries)


def get_firestore_client():
    return firestore.Client(
        project="local-project"
    )


def save_summary_to_firestore(customer_id, summary):
    db = get_firestore_client()

    db.collection("customer_aggregates").document(customer_id).set(summary)


if __name__ == "__main__":
    aggregate_customer_stats(None, None)