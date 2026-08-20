import json
import logging

from MySql.MySql import insert_event


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


def event_writer(event, context):

    try:
        # Pub/Sub message data arrives as bytes.
        incoming_message = event["data"]

        # Convert bytes -> string.
        incoming_message = incoming_message.decode("utf-8")

        # Convert JSON string -> Python dictionary.
        event_data = json.loads(incoming_message)

        # Validate before writing to MySQL.
        validation(event_data)

        # Store the event.
        insert_event(event_data)

    except Exception as error:

        logging.exception(
            f"Failed to process Pub/Sub message: {error}"
        )

        return


def validation(data):

    # Event must be a dictionary.
    if not isinstance(data, dict):
        raise ValueError("invalid event data")

    # Validate required fields.
    for field in required_fields:

        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"invalid or missing field: {field}"
            )

    # Validate event type.
    if data.get("event_type") not in allowed_event_types:
        raise ValueError(
            "Event Type is not correct"
        )

    # Purchase events require a numeric value.
    if data.get("event_type") == "purchase":

        purchase_value = data.get("value")

        if (
            isinstance(purchase_value, bool)
            or not isinstance(
                purchase_value,
                (int, float)
            )
        ):
            raise ValueError(
                "invalid or missing purchase value"
            )