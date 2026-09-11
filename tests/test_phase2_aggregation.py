"""Tests for the MySQL-to-Firestore aggregation."""

import os
from datetime import datetime

from google.cloud import firestore

from aggregate_function.main import aggregate_events


# The tests use the Firestore emulator started by Docker Compose.
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"


def test_aggregate_events_correct_totals():
    events = [
        {
            "customer_id": "cust_1",
            "event_type": "view",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 10, 0),
        },
        {
            "customer_id": "cust_1",
            "event_type": "purchase",
            "value": 50.0,
            "event_timestamp": datetime(2026, 8, 20, 11, 0),
        },
        {
            "customer_id": "cust_1",
            "event_type": "purchase",
            "value": 25.0,
            "event_timestamp": datetime(2026, 8, 20, 12, 0),
        },
    ]

    customer = aggregate_events(events)["cust_1"]

    assert customer["total_events"] == 3
    assert customer["purchase_count"] == 2
    assert customer["total_value"] == 75.0
    assert customer["last_event_at"] == datetime(2026, 8, 20, 12, 0)


def test_customer_with_no_purchases():
    events = [
        {
            "customer_id": "cust_2",
            "event_type": "view",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 10, 0),
        },
        {
            "customer_id": "cust_2",
            "event_type": "add_to_cart",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 11, 0),
        },
    ]

    customer = aggregate_events(events)["cust_2"]

    assert customer["total_events"] == 2
    assert customer["purchase_count"] == 0
    assert customer["total_value"] == 0
    assert customer["last_event_at"] == datetime(2026, 8, 20, 11, 0)


def test_aggregation_is_idempotent():
    events = [
        {
            "customer_id": "cust_3",
            "event_type": "purchase",
            "value": 40.0,
            "event_timestamp": datetime(2026, 8, 20, 10, 0),
        },
        {
            "customer_id": "cust_3",
            "event_type": "view",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 11, 0),
        },
    ]

    first = aggregate_events(events)["cust_3"]
    second = aggregate_events(events)["cust_3"]

    assert first["total_events"] == second["total_events"] == 2
    assert first["purchase_count"] == second["purchase_count"] == 1
    assert first["total_value"] == second["total_value"] == 40.0


def test_firestore_readback():
    db = firestore.Client(project="local-project")
    customer_id = "test_customer"
    data = {
        "customer_id": customer_id,
        "total_events": 3,
        "total_value": 75.0,
        "purchase_count": 2,
        "last_event_at": datetime(2026, 8, 20, 12, 0),
        "updated_at": datetime(2026, 8, 20, 13, 0),
    }

    reference = db.collection("customer_aggregates").document(customer_id)
    reference.set(data)
    saved_data = reference.get().to_dict()

    assert saved_data["customer_id"] == customer_id
    assert saved_data["total_events"] == 3
    assert saved_data["total_value"] == 75.0
    assert saved_data["purchase_count"] == 2


def test_firestore_idempotency():
    db = firestore.Client(project="local-project")
    customer_id = "idempotent_customer"
    data = {
        "customer_id": customer_id,
        "total_events": 2,
        "total_value": 40.0,
        "purchase_count": 1,
    }

    reference = db.collection("customer_aggregates").document(customer_id)
    reference.set(data)
    reference.set(data)
    saved_data = reference.get().to_dict()

    assert saved_data["customer_id"] == customer_id
    assert saved_data["total_events"] == 2
    assert saved_data["total_value"] == 40.0
    assert saved_data["purchase_count"] == 1
