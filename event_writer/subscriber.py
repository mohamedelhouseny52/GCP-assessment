import os

from google.cloud import pubsub_v1

from event_writer.event_writer import event_writer


project_id = os.getenv(
    "PUBSUB_PROJECT_ID",
    "local-project"
)

subscription_id = os.getenv(
    "PUBSUB_SUBSCRIPTION",
    "event-writer-sub"
)


subscriber = pubsub_v1.SubscriberClient()

subscription_path = subscriber.subscription_path(
    project_id,
    subscription_id
)


def callback(message):

    event = {
        "data": message.data
    }

    event_writer(
        event,
        None
    )

    message.ack()


streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=callback
)


print(
    "Listening for Pub/Sub messages..."
)


try:
    streaming_pull_future.result()

except KeyboardInterrupt:

    streaming_pull_future.cancel()

    print(
        "Subscriber stopped."
    )