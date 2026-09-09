"""Beginner-friendly tests for the Phase 1 HTTP function."""

from flask import Flask, request

import ingest_function.main as main


app = Flask(__name__)


def call_ingest(body):
    """Call the function without running a web server."""
    with app.test_request_context(
        "/events/ingest",
        method="POST",
        json=body,
    ):
        return main.ingest_event(request)


def valid_event():
    return {
        "customer_id": "customer_1",
        "event_type": "purchase",
        "product_id": "product_1",
        "value": 49.99,
        "timestamp": "2026-08-20T10:00:00Z",
    }


def test_ingest_valid_event_returns_202(monkeypatch):
    published = []
    monkeypatch.setattr(main, "publish_event", published.append)

    response, status = call_ingest(valid_event())

    assert status == 202
    assert response.get_json() == {"status": "queued"}
    assert published[0]["customer_id"] == "customer_1"


def test_ingest_missing_customer_id_returns_400(monkeypatch):
    monkeypatch.setattr(main, "publish_event", lambda event: None)
    event = valid_event()
    del event["customer_id"]

    response, status = call_ingest(event)

    assert status == 400
    assert "customer_id" in response.get_json()["error"]


def test_ingest_invalid_event_type_returns_400(monkeypatch):
    monkeypatch.setattr(main, "publish_event", lambda event: None)
    event = valid_event()
    event["event_type"] = "login"

    response, status = call_ingest(event)

    assert status == 400


def test_ingest_purchase_without_value_returns_400(monkeypatch):
    monkeypatch.setattr(main, "publish_event", lambda event: None)
    event = valid_event()
    del event["value"]

    response, status = call_ingest(event)

    assert status == 400
    assert "value" in response.get_json()["error"]
