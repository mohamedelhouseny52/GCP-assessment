"""HTTP function that validates and queues customer events."""

import json
import logging
import os
from datetime import datetime, timezone
from functools import lru_cache

import functions_framework
from flask import jsonify
from google.cloud import pubsub_v1


# Supported event types and required request fields.
ALLOWED_EVENT_TYPES = ["view", "add_to_cart", "purchase"]
REQUIRED_FIELDS = ["event_type", "customer_id", "product_id", "timestamp"]


def validate_event(data):
    """Check one event and return (clean_event, error_message)."""
    if not isinstance(data, dict):
        return None, "request body must be valid JSON"

    for field in REQUIRED_FIELDS:
        if field not in data:
            return None, f"required {field} is missing"

    event_type = data["event_type"]
    customer_id = data["customer_id"]
    product_id = data["product_id"]
    timestamp = data["timestamp"]
    value = data.get("value")

    if event_type not in ALLOWED_EVENT_TYPES:
        return None, "event_type is not correct"
    if not isinstance(customer_id, str) or not customer_id.strip():
        return None, "invalid or missing customer_id"
    if not isinstance(product_id, str) or not product_id.strip():
        return None, "invalid or missing product_id"
    if not isinstance(timestamp, str) or not timestamp.strip():
        return None, "invalid or missing timestamp"

    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed_timestamp.tzinfo is None:
            parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)
        utc_timestamp = parsed_timestamp.astimezone(timezone.utc)
    except ValueError:
        return None, "timestamp must be a valid ISO-8601 timestamp"

    if event_type == "purchase":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, "value is required for purchase events and must be numeric"
    else:
        value = None

    clean_event = {
        "event_type": event_type,
        "customer_id": customer_id.strip(),
        "product_id": product_id.strip(),
        "value": value,
        "timestamp": utc_timestamp.isoformat().replace("+00:00", "Z"),
    }
    return clean_event, None


@lru_cache(maxsize=1)
def get_publisher():
    return pubsub_v1.PublisherClient()


def publish_event(event):
    """Send one event to the raw-events Pub/Sub topic."""
    project_id = os.getenv("PUBSUB_PROJECT_ID", "local-project")
    topic_id = os.getenv("PUBSUB_TOPIC", "raw-events")

    # The client uses Pub/Sub or its configured emulator.
    publisher = get_publisher()
    topic_path = publisher.topic_path(project_id, topic_id)
    message = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, message)

    # Confirm publication before returning HTTP 202.
    future.result(timeout=10)


@functions_framework.http
def ingest_event(request):
    """Handle POST /events/ingest."""
    if request.method != "POST":
        return jsonify({"error": "method not allowed"}), 405

    event, error = validate_event(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    try:
        publish_event(event)
    except Exception:
        logging.exception("Could not publish event")
        return jsonify({"error": "event could not be queued"}), 503

    return jsonify({"status": "queued"}), 202
