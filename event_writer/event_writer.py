"""Convert Pub/Sub messages into MySQL rows."""

import json
import logging

from MySql.MySql import insert_event


ALLOWED_EVENT_TYPES = ["view", "add_to_cart", "purchase"]
REQUIRED_FIELDS = ["event_type", "customer_id", "product_id", "timestamp"]


def validate_event(data):
    """Raise ValueError when a Pub/Sub event is not valid."""
    if not isinstance(data, dict):
        raise ValueError("event must be a JSON object")

    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"invalid or missing field: {field}")

    if data["event_type"] not in ALLOWED_EVENT_TYPES:
        raise ValueError("event_type is not correct")

    if data["event_type"] == "purchase":
        value = data.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("invalid or missing purchase value")


def event_writer(event, context=None):
    """Process one Pub/Sub event.

    Bad JSON is logged and ignored. Database errors are allowed to escape so
    the subscriber can leave the message unacknowledged and retry it.
    """
    # Only the message-reading part is inside this try block.
    # A database error must escape so Pub/Sub can retry the message.
    try:
        raw_data = event["data"]
        raw_data = raw_data.decode("utf-8")
        data = json.loads(raw_data)
        validate_event(data)
    except Exception as error:
        logging.error("Ignoring malformed Pub/Sub event: %s", error)
        return False

    # If MySQL fails, this line raises an error and the subscriber does not
    # acknowledge the message.
    insert_event(data)
    return True
