"""Long-running Pub/Sub subscriber for the event writer."""

import logging
import os

from google.cloud import pubsub_v1

from event_writer.event_writer import event_writer


def callback(message):
    """Write one message, then acknowledge it."""
    try:
        event_writer({"data": message.data})
    except Exception:
        logging.exception("Database error; Pub/Sub will retry the message")
        return

    message.ack()


def main():
    project_id = os.getenv("PUBSUB_PROJECT_ID", "local-project")
    subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "event-writer-sub")

    subscriber = pubsub_v1.SubscriberClient()
    path = subscriber.subscription_path(project_id, subscription_id)
    future = subscriber.subscribe(path, callback=callback)

    print("Listening for Pub/Sub messages...", flush=True)
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()
        print("Subscriber stopped.", flush=True)


if __name__ == "__main__":
    main()
