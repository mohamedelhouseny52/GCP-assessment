import json

from event_writer.event_writer import event_writer

test_event = {
    "event_type": "purchase",
    "customer_id": "cust_123",
    "product_id": "prod_456",
    "timestamp": "2026-08-20 13:20:00",
    "value": 49.99
}

message = json.dumps(test_event).encode("utf-8")

fake_pubsub_event = {
    "data": message
}

event_writer(fake_pubsub_event, None)

bad_pubsub_event = {
    "data": b"this is not valid json"
}

event_writer(bad_pubsub_event, None)