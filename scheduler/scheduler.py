from google.cloud import pubsub_v1


def trigger_aggregation():
    publisher = pubsub_v1.PublisherClient()

    project_id = "local-project"
    topic_id = "run-aggregation"

    topic_path = publisher.topic_path(project_id, topic_id)

    message = b"run"

    publish_future = publisher.publish(
        topic_path,
        message
    )

    publish_future.result(timeout=10)

print("Aggregation trigger sent")


if __name__ == "__main__":
    trigger_aggregation()