"""Tests for the customer summary HTTP endpoint."""

import os
from unittest.mock import Mock

from flask import Flask, request
from google.cloud import firestore

import summary_api.main as main


os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"
app = Flask(__name__)


def call_api(path):
    with app.test_request_context(path, method="GET"):
        return main.summary_api(request)


def test_summary_returns_200_for_known_customer():
    db = firestore.Client(project="local-project")
    customer_id = "phase3_known_customer"
    db.collection("customer_aggregates").document(customer_id).set(
        {
            "customer_id": customer_id,
            "total_events": 3,
            "total_value": 75.0,
            "purchase_count": 2,
            "last_event_at": "2026-08-20T12:00:00Z",
            "updated_at": "2026-08-20T13:00:00Z",
        }
    )

    response, status = call_api(f"/customers/{customer_id}/summary")

    assert status == 200
    assert response.get_json()["customer_id"] == customer_id
    assert response.get_json()["total_events"] == 3
    assert response.get_json()["total_value"] == 75.0


def test_summary_returns_404_for_unknown_customer():
    response, status = call_api("/customers/customer_that_does_not_exist/summary")

    assert status == 404
    assert response.get_json() == {"error": "customer not found"}


def test_summary_returns_503_when_firestore_unreachable(monkeypatch):
    def broken_firestore(customer_id):
        raise Exception("Firestore unavailable")

    monkeypatch.setattr(main, "get_customer_summary", broken_firestore)
    response, status = call_api("/customers/cust_123/summary")

    assert status == 503
    assert response.get_json() == {"error": "service unavailable"}


def test_summary_returns_500_for_malformed_document():
    db = firestore.Client(project="local-project")
    customer_id = "malformed_customer"
    db.collection("customer_aggregates").document(customer_id).set(
        {"customer_id": customer_id, "total_events": 3}
    )

    response, status = call_api(f"/customers/{customer_id}/summary")

    assert status == 500
    assert response.get_json() == {"error": "internal server error"}


def test_summary_rejects_blank_customer_id(monkeypatch):
    get_summary = Mock()
    monkeypatch.setattr(main, "get_customer_summary", get_summary)

    response, status = call_api("/customers/%20/summary")

    assert status == 400
    assert response.get_json() == {"error": "invalid customer_id"}
    get_summary.assert_not_called()


def test_summary_uses_configured_project_and_reuses_client(monkeypatch):
    client_factory = Mock()
    monkeypatch.setenv("GCP_PROJECT_ID", "assessment-project")
    monkeypatch.setattr(main.firestore, "Client", client_factory)
    main.get_firestore_client.cache_clear()

    try:
        main.get_firestore_client()
        main.get_firestore_client()
        client_factory.assert_called_once_with(project="assessment-project")
    finally:
        main.get_firestore_client.cache_clear()
