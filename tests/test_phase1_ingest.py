"""Tests for the Phase 1 HTTP function."""

import json
from unittest.mock import Mock

import pytest
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


@pytest.fixture
def publisher(monkeypatch):
    client = Mock()
    client.topic_path.return_value = "projects/local-project/topics/raw-events"
    client.publish.return_value.result.return_value = "message-id"
    factory = Mock(return_value=client)
    monkeypatch.setattr(main.pubsub_v1, "PublisherClient", factory)
    main.get_publisher.cache_clear()
    yield client, factory
    main.get_publisher.cache_clear()


def test_ingest_valid_event_returns_202(publisher):
    client, _ = publisher

    response, status = call_ingest(valid_event())

    assert status == 202
    assert response.get_json() == {"status": "queued"}
    topic_path, payload = client.publish.call_args.args
    assert topic_path == "projects/local-project/topics/raw-events"
    assert json.loads(payload)["customer_id"] == "customer_1"
    client.publish.return_value.result.assert_called_once_with(timeout=10)


def test_ingest_missing_customer_id_returns_400(publisher):
    client, _ = publisher
    event = valid_event()
    del event["customer_id"]

    response, status = call_ingest(event)

    assert status == 400
    assert "customer_id" in response.get_json()["error"]
    client.publish.assert_not_called()


def test_ingest_invalid_event_type_returns_400(publisher):
    client, _ = publisher
    event = valid_event()
    event["event_type"] = "login"

    response, status = call_ingest(event)

    assert status == 400
    client.publish.assert_not_called()


def test_ingest_purchase_without_value_returns_400(publisher):
    client, _ = publisher
    event = valid_event()
    del event["value"]

    response, status = call_ingest(event)

    assert status == 400
    assert "value" in response.get_json()["error"]
    client.publish.assert_not_called()


def test_ingest_normalizes_offset_timestamp_to_utc(publisher):
    client, _ = publisher
    event = valid_event()
    event["timestamp"] = "2026-08-20T13:00:00+03:00"

    _, status = call_ingest(event)

    assert status == 202
    assert json.loads(client.publish.call_args.args[1])["timestamp"] == (
        "2026-08-20T10:00:00Z"
    )


def test_ingest_treats_naive_timestamp_as_utc(publisher):
    client, _ = publisher
    event = valid_event()
    event["timestamp"] = "2026-08-20T10:00:00"

    _, status = call_ingest(event)

    assert status == 202
    assert json.loads(client.publish.call_args.args[1])["timestamp"] == (
        "2026-08-20T10:00:00Z"
    )


def test_publish_reuses_client(publisher):
    _, factory = publisher

    main.publish_event(valid_event())
    main.publish_event(valid_event())

    factory.assert_called_once_with()
