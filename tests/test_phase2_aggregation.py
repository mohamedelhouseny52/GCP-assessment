from datetime import datetime

from aggregate_function.main import aggregate_events


def test_aggregate_events_correct_totals():

    events = [
        {
            "customer_id": "cust_1",
            "event_type": "view",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 10, 0)
        },
        {
            "customer_id": "cust_1",
            "event_type": "purchase",
            "value": 50.0,
            "event_timestamp": datetime(2026, 8, 20, 11, 0)
        },
        {
            "customer_id": "cust_1",
            "event_type": "purchase",
            "value": 25.0,
            "event_timestamp": datetime(2026, 8, 20, 12, 0)
        }
    ]

    result = aggregate_events(events)

    customer = result["cust_1"]

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
            "event_timestamp": datetime(2026, 8, 20, 10, 0)
        },
        {
            "customer_id": "cust_2",
            "event_type": "add_to_cart",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 11, 0)
        }
    ]

    result = aggregate_events(events)

    customer = result["cust_2"]

    assert customer["total_events"] == 2
    assert customer["purchase_count"] == 0
    assert customer["total_value"] == 0
    assert customer["last_event_at"] == datetime(2026, 8, 20, 11, 0)


import os

from google.cloud import firestore


def test_firestore_readback():

    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"

    db = firestore.Client(project="local-project")

    customer_id = "test_customer"

    test_data = {
        "customer_id": customer_id,
        "total_events": 3,
        "total_value": 75.0,
        "purchase_count": 2,
        "last_event_at": datetime(2026, 8, 20, 12, 0),
        "updated_at": datetime(2026, 8, 20, 13, 0)
    }

    document_ref = (
        db.collection("customer_aggregates")
        .document(customer_id)
    )

    document_ref.set(test_data)

    document = document_ref.get()

    assert document.exists

    saved_data = document.to_dict()

    assert saved_data["customer_id"] == customer_id
    assert saved_data["total_events"] == 3
    assert saved_data["total_value"] == 75.0
    assert saved_data["purchase_count"] == 2


def test_aggregation_is_idempotent():
    
    events = [
        {
            "customer_id": "cust_3",
            "event_type": "purchase",
            "value": 40.0,
            "event_timestamp": datetime(2026, 8, 20, 10, 0)
        },
        {
            "customer_id": "cust_3",
            "event_type": "view",
            "value": None,
            "event_timestamp": datetime(2026, 8, 20, 11, 0)
        }
    ]

    first_result = aggregate_events(events)
    second_result = aggregate_events(events)

    assert first_result["cust_3"]["total_events"] == 2
    assert second_result["cust_3"]["total_events"] == 2

    assert first_result["cust_3"]["purchase_count"] == 1
    assert second_result["cust_3"]["purchase_count"] == 1

    assert first_result["cust_3"]["total_value"] == 40.0
    assert second_result["cust_3"]["total_value"] == 40.0

def test_firestore_idempotency():
    
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"

    db = firestore.Client(project="local-project")

    customer_id = "idempotent_customer"

    document_ref = (
        db.collection("customer_aggregates")
        .document(customer_id)
    )

    first_data = {
        "customer_id": customer_id,
        "total_events": 2,
        "total_value": 40.0,
        "purchase_count": 1
    }

    second_data = {
        "customer_id": customer_id,
        "total_events": 2,
        "total_value": 40.0,
        "purchase_count": 1
    }

    document_ref.set(first_data)
    document_ref.set(second_data)

    document = document_ref.get()

    assert document.exists

    saved_data = document.to_dict()

    assert saved_data["customer_id"] == customer_id
    assert saved_data["total_events"] == 2
    assert saved_data["total_value"] == 40.0
    assert saved_data["purchase_count"] == 1