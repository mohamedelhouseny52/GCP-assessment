"""Optional manual example for the Phase 1 event writer.

Run it explicitly with:

    python manual_test.py
"""

import json

from event_writer.event_writer import event_writer


def main():
    valid_event = {
        "event_type": "purchase",
        "customer_id": "cust_123",
        "product_id": "prod_456",
        "timestamp": "2026-08-20T13:20:00Z",
        "value": 49.99,
    }

    event_writer({"data": json.dumps(valid_event).encode("utf-8")})
    event_writer({"data": b"this is not valid json"})


if __name__ == "__main__":
    main()
