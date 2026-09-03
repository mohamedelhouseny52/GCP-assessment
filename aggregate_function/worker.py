from google.cloud import pubsub_v1
from aggregate_function.main import aggregate_customer_stats


PROJECT_ID = "local-project"
SUBSCRIPTION_ID = "aggregation-sub"


def callback(message):
    print("Aggregation trigger received")

    aggregate_customer_stats(None, None)

    message.ack()


def start_worker():
    subscriber = pubsub_v1.SubscriberClient()

    subscription_path = subscriber.subscription_path(
        PROJECT_ID,
        SUBSCRIPTION_ID
    )

    future = subscriber.subscribe(
        subscription_path,
        callback=callback
    )

    print("Waiting for aggregation triggers...")

    future.result()


if __name__ == "__main__":
    start_worker()