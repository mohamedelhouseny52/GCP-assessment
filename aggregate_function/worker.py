"""Listen for aggregation triggers."""

import logging
import os

from google.cloud import pubsub_v1

from aggregate_function.main import aggregate_customer_stats


def callback(message):
    try:
        aggregate_customer_stats()
    except Exception:
        logging.exception("Aggregation failed; Pub/Sub will retry the trigger")
        return

    message.ack()
    print("Aggregation trigger received", flush=True)


def main():
    project_id = os.getenv("PUBSUB_PROJECT_ID", "local-project")
    subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "aggregation-sub")

    subscriber = pubsub_v1.SubscriberClient()
    path = subscriber.subscription_path(project_id, subscription_id)
    future = subscriber.subscribe(path, callback=callback)

    print("Waiting for aggregation triggers...", flush=True)
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()


if __name__ == "__main__":
    main()
