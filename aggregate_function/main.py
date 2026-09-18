"""Read events from MySQL and save one summary per customer in Firestore."""

import os
from datetime import datetime, timezone

from google.cloud import firestore

from MySql.MySql import get_connection


def get_events():
    """Return every event needed for an all-time aggregation."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT customer_id, event_type, value, event_timestamp
            FROM events
            """
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def aggregate_events(events):
    """Calculate customer totals from event rows."""
    summaries = {}

    for event in events:
        customer_id = event["customer_id"]
        if customer_id not in summaries:
            summaries[customer_id] = {
                "customer_id": customer_id,
                "total_events": 0,
                "total_value": 0.0,
                "purchase_count": 0,
                "last_event_at": None,
            }

        summary = summaries[customer_id]

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
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id and os.getenv("FIRESTORE_EMULATOR_HOST"):
        project_id = "local-project"
    return firestore.Client(project=project_id) if project_id else firestore.Client()


def save_summary_to_firestore(db, customer_id, summary):
    """Replace one document, which makes repeated runs idempotent."""
    db.collection("customer_aggregates").document(customer_id).set(summary)


def aggregate_customer_stats(event=None, context=None):
    """Recalculate all customers and write their Firestore documents."""
    lock_connection = get_connection()
    lock_cursor = None
    try:
        lock_cursor = lock_connection.cursor()
        lock_cursor.execute("SELECT GET_LOCK('customer_aggregation', 30)")
        if lock_cursor.fetchone()[0] != 1:
            raise TimeoutError("Could not acquire aggregation lock")
        try:
            summaries = aggregate_events(get_events())
            if summaries:
                db = get_firestore_client()
                for customer_id, summary in summaries.items():
                    save_summary_to_firestore(db, customer_id, summary)
        finally:
            lock_cursor.execute("SELECT RELEASE_LOCK('customer_aggregation')")
            if lock_cursor.fetchone()[0] != 1:
                raise RuntimeError("Could not release aggregation lock")
    finally:
        try:
            if lock_cursor is not None:
                lock_cursor.close()
        finally:
            lock_connection.close()

    print(f"Aggregated {len(summaries)} customers", flush=True)


if __name__ == "__main__":
    aggregate_customer_stats()
