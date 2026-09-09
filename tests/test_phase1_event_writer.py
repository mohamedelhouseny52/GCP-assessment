"""Beginner-friendly tests for the Phase 1 Pub/Sub consumer."""

import json

import event_writer.event_writer as writer


def valid_event():
    return {
        "customer_id": "customer_1",
        "event_type": "purchase",
        "product_id": "product_1",
        "value": 49.99,
        "timestamp": "2026-08-20T10:00:00Z",
    }


def test_event_writer_inserts_row_correctly(monkeypatch):
    inserted = []
    monkeypatch.setattr(writer, "insert_event", inserted.append)

    result = writer.event_writer(
        {"data": json.dumps(valid_event()).encode("utf-8")}
    )

    assert result is True
    assert inserted == [valid_event()]


def test_event_writer_handles_malformed_pubsub_message_gracefully():
    result = writer.event_writer({"data": b"this is not JSON"})

    assert result is False
