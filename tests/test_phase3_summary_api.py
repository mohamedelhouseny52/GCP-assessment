import os

from flask import Flask
from google.cloud import firestore

import summary_api.main as main


os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"

app = Flask(__name__)


def test_summary_returns_200_for_known_customer():

    db = firestore.Client(project="local-project")

    customer_id = "phase3_known_customer"

    test_data = {
        "customer_id": customer_id,
        "total_events": 3,
        "total_value": 75.0,
        "purchase_count": 2,
        "last_event_at": "2026-08-20T12:00:00Z",
        "updated_at": "2026-08-20T13:00:00Z",
    }

    db.collection(
        "customer_aggregates"
    ).document(
        customer_id
    ).set(
        test_data
    )

    with app.test_request_context(
        f"/customers/{customer_id}/summary",
        method="GET"
    ):
        from flask import request

        response, status_code = main.summary_api(request)

    assert status_code == 200

    data = response.get_json()

    assert data["customer_id"] == customer_id
    assert data["total_events"] == 3
    assert data["total_value"] == 75.0
    assert data["purchase_count"] == 2


def test_summary_returns_404_for_unknown_customer():

    customer_id = "customer_that_does_not_exist"

    with app.test_request_context(
        f"/customers/{customer_id}/summary",
        method="GET"
    ):
        from flask import request

        response, status_code = main.summary_api(request)

    assert status_code == 404

    assert response.get_json() == {
        "error": "customer not found"
    }


def test_summary_returns_503_when_firestore_unreachable(
    monkeypatch
):

    def broken_firestore(customer_id):
        raise Exception("Firestore unavailable")

    monkeypatch.setattr(
        main,
        "get_customer_summary",
        broken_firestore
    )

    with app.test_request_context(
        "/customers/cust_123/summary",
        method="GET"
    ):
        from flask import request

        response, status_code = main.summary_api(request)

    assert status_code == 503

    assert response.get_json() == {
        "error": "service unavailable"
    }


def test_summary_returns_500_for_malformed_document():

    db = firestore.Client(project="local-project")

    customer_id = "malformed_customer"

    malformed_data = {
        "customer_id": customer_id,
        "total_events": 3
    }

    db.collection(
        "customer_aggregates"
    ).document(
        customer_id
    ).set(
        malformed_data
    )

    with app.test_request_context(
        f"/customers/{customer_id}/summary",
        method="GET"
    ):
        from flask import request

        response, status_code = main.summary_api(request)

    assert status_code == 500

    assert response.get_json() == {
        "error": "internal server error"
    }