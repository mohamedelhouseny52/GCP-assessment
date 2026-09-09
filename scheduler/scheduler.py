"""Publish the message that starts customer aggregation."""

import os

from google.cloud import pubsub_v1


def trigger_aggregation():
    project_id = os.getenv("PUBSUB_PROJECT_ID", "local-project")
    topic_id = os.getenv("PUBSUB_TOPIC", "run-aggregation")

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    publisher.publish(topic_path, b"run").result(timeout=10)
    print("Aggregation trigger sent", flush=True)


if __name__ == "__main__":
    trigger_aggregation()
