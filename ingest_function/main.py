import os
import json
from datetime import datetime

import functions_framework
from flask import jsonify
from google.cloud import pubsub_v1


required_fields = [
    "event_type",
    "customer_id",
    "product_id",
    "timestamp"
]

allowed_event_types = [
    "add_to_cart",
    "view",
    "purchase"
]


@functions_framework.http
def ingest_event(request):

    # Only POST requests are allowed.
    if request.method != "POST":
        return jsonify({
            "error": "method not allowed"
        }), 405

    # Read the JSON request body.
    request_body = request.get_json(silent=True)

    if not isinstance(request_body, dict):
        return jsonify({
            "error": "request body must be valid JSON"
        }), 400

    # Check required fields.
    for field in required_fields:
        if field not in request_body:
            return jsonify({
                "error": f"required {field} is missing"
            }), 400

    event_type = request_body["event_type"]
    customer_id = request_body["customer_id"]
    product_id = request_body["product_id"]
    timestamp = request_body["timestamp"]

    # value is optional except for purchase events.
    value = request_body.get("value")

    # Validate event type.
    if event_type not in allowed_event_types:
        return jsonify({
            "error": "event_type is not correct"
        }), 400

    # Validate customer ID.
    if not isinstance(customer_id, str) or not customer_id.strip():
        return jsonify({
            "error": "invalid or missing customer_id"
        }), 400

    # Validate product ID.
    if not isinstance(product_id, str) or not product_id.strip():
        return jsonify({
            "error": "invalid or missing product_id"
        }), 400

    # Validate timestamp.
    if not isinstance(timestamp, str) or not timestamp.strip():
        return jsonify({
            "error": "invalid or missing timestamp"
        }), 400

    try:
        datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

    except ValueError:
        return jsonify({
            "error": "timestamp must be a valid ISO-8601 timestamp"
        }), 400

    # Purchase events require a numeric value.
    if event_type == "purchase":

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            return jsonify({
                "error": "value is required for purchase events and must be numeric"
            }), 400

    # Build the event that will be sent to Pub/Sub.
    event_data = {
        "event_type": event_type,
        "customer_id": customer_id.strip(),
        "product_id": product_id.strip(),
        "timestamp": timestamp,
        "value": value if event_type == "purchase" else None
    }

    # Convert dictionary -> JSON -> bytes.
    message = json.dumps(event_data).encode("utf-8")

    # These values work locally by default.
    # Docker can override them using environment variables.
    project_id = os.getenv(
        "PUBSUB_PROJECT_ID",
        "local-project"
    )

    topic_id = os.getenv(
        "PUBSUB_TOPIC",
        "raw-events"
    )

    publisher = pubsub_v1.PublisherClient()

    topic_path = publisher.topic_path(
        project_id,
        topic_id
    )

    try:
        future = publisher.publish(
            topic_path,
            message
        )

        # Wait until Pub/Sub confirms that it accepted the message.
        future.result(timeout=10)

    except Exception:
        return jsonify({
            "error": "event could not be queued"
        }), 503

    return jsonify({
        "status": "queued"
    }), 202