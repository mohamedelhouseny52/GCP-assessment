"""Read events from MySQL and save one summary per customer in Firestore."""

from datetime import datetime, timezone

from google.cloud import firestore

from MySql.MySql import get_connection


def get_events():
    """Return every event needed for an all-time aggregation."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT customer_id, event_type, value, event_timestamp
        FROM events
        """
    )
    events = cursor.fetchall()
    cursor.close()
    connection.close()
    return events


def aggregate_events(events):
    """Calculate totals in Python so the rule is easy to see."""
    summaries = {}

    for event in events:
        customer_id = event["customer_id"]
        summary = summaries.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "total_events": 0,
                "total_value": 0.0,
                "purchase_count": 0,
                "last_event_at": None,
            },
        )

        summary["total_events"] += 1

        if event["event_type"] == "purchase":
            summary["purchase_count"] += 1
            summary["total_value"] += float(event["value"] or 0)

        event_time = event["event_timestamp"]
        if (
            summary["last_event_at"] is None
            or event_time > summary["last_event_at"]
        ):
            summary["last_event_at"] = event_time

    updated_at = datetime.now(timezone.utc)
    for summary in summaries.values():
        summary["updated_at"] = updated_at

    return summaries


def get_firestore_client():
    return firestore.Client(project="local-project")


def save_summary_to_firestore(customer_id, summary, db=None):
    """Replace one document, which makes repeated runs idempotent."""
    db = db or get_firestore_client()
    db.collection("customer_aggregates").document(customer_id).set(summary)


def aggregate_customer_stats(event=None, context=None):
    """Recalculate all customers and write their Firestore documents."""
    summaries = aggregate_events(get_events())
    db = get_firestore_client()

    for customer_id, summary in summaries.items():
        save_summary_to_firestore(customer_id, summary, db)

    print(f"Aggregated {len(summaries)} customers", flush=True)


if __name__ == "__main__":
    aggregate_customer_stats()
