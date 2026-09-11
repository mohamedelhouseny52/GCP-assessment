"""Create sample customers and events for local testing."""

import random
from datetime import datetime, timedelta

from MySql.MySql import get_connection


CUSTOMER_COUNT = 50
RANDOM_SEED = 42


def insert_event(cursor, customer_id, event_type, product_id, value, event_time):
    """Insert one event using the same table as the real event writer."""
    query = """
        INSERT INTO events
            (customer_id, event_type, product_id, value, event_timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(
        query,
        (customer_id, event_type, product_id, value, event_time),
    )


def random_product():
    return f"product_{random.randint(1, 20):03d}"


def generate_purchase_values(is_high_value):
    if is_high_value:
        values = [round(random.uniform(80, 180), 2) for _ in range(random.randint(2, 5))]
        if sum(values) <= 200:
            values[0] += 201 - sum(values)
        return values

    values = [round(random.uniform(10, 70), 2) for _ in range(random.randint(0, 3))]
    while values and sum(values) > 200:
        values[-1] = round(values[-1] / 2, 2)
    return values


def generate_events():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()
    inserted_events = 0

    for customer_number in range(1, CUSTOMER_COUNT + 1):
        customer_id = f"sample_customer_{customer_number:03d}"
        is_high_value = customer_number > 25
        view_count = random.randint(1, 8)
        cart_count = random.randint(0, 5)
        purchase_values = generate_purchase_values(is_high_value)
        start_time = datetime.now() - timedelta(days=random.randint(1, 30))

        # Add views, cart actions, and purchases for this customer.
        for number in range(view_count):
            insert_event(
                cursor,
                customer_id,
                "view",
                random_product(),
                None,
                start_time + timedelta(minutes=number),
            )
            inserted_events += 1

        for number in range(cart_count):
            insert_event(
                cursor,
                customer_id,
                "add_to_cart",
                random_product(),
                None,
                start_time + timedelta(hours=1, minutes=number),
            )
            inserted_events += 1

        for number, value in enumerate(purchase_values):
            insert_event(
                cursor,
                customer_id,
                "purchase",
                random_product(),
                value,
                start_time + timedelta(hours=2, minutes=number),
            )
            inserted_events += 1

    connection.commit()
    cursor.close()
    connection.close()
    print(f"Created {CUSTOMER_COUNT} sample customers")
    print(f"Inserted {inserted_events} sample events")


if __name__ == "__main__":
    generate_events()
