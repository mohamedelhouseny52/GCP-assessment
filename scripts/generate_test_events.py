import os
import random
from datetime import datetime, timedelta

import mysql.connector


CUSTOMER_COUNT = 50
RANDOM_SEED = 42


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "event_db"),
    )


def generate_events():
    random.seed(RANDOM_SEED)

    connection = get_connection()
    cursor = connection.cursor()

    inserted_events = 0

    for customer_number in range(1, CUSTOMER_COUNT + 1):
        customer_id = f"sample_customer_{customer_number:03d}"

        # Make roughly half low-value and half high-value customers.
        high_value_customer = customer_number > 25

        view_count = random.randint(1, 8)
        cart_count = random.randint(0, 5)

        if high_value_customer:
            purchase_count = random.randint(2, 5)
            purchase_values = [
                round(random.uniform(80, 180), 2)
                for _ in range(purchase_count)
            ]

            # Guarantee total_value > 200.
            if sum(purchase_values) <= 200:
                purchase_values[0] += 201 - sum(purchase_values)

        else:
            purchase_count = random.randint(0, 3)

            purchase_values = [
                round(random.uniform(10, 70), 2)
                for _ in range(purchase_count)
            ]

            # Guarantee total_value <= 200.
            while sum(purchase_values) > 200:
                purchase_values[-1] = round(
                    purchase_values[-1] / 2,
                    2
                )

        base_time = datetime.now() - timedelta(
            days=random.randint(1, 30)
        )

        # Views
        for i in range(view_count):
            cursor.execute(
                """
                INSERT INTO events (
                    customer_id,
                    event_type,
                    product_id,
                    value,
                    event_timestamp
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    customer_id,
                    "view",
                    f"product_{random.randint(1, 20):03d}",
                    None,
                    base_time + timedelta(minutes=i),
                ),
            )

            inserted_events += 1

        # Add to cart
        for i in range(cart_count):
            cursor.execute(
                """
                INSERT INTO events (
                    customer_id,
                    event_type,
                    product_id,
                    value,
                    event_timestamp
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    customer_id,
                    "add_to_cart",
                    f"product_{random.randint(1, 20):03d}",
                    None,
                    base_time + timedelta(
                        hours=1,
                        minutes=i,
                    ),
                ),
            )

            inserted_events += 1

        # Purchases
        for i, purchase_value in enumerate(purchase_values):
            cursor.execute(
                """
                INSERT INTO events (
                    customer_id,
                    event_type,
                    product_id,
                    value,
                    event_timestamp
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    customer_id,
                    "purchase",
                    f"product_{random.randint(1, 20):03d}",
                    purchase_value,
                    base_time + timedelta(
                        hours=2,
                        minutes=i,
                    ),
                ),
            )

            inserted_events += 1

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Created {CUSTOMER_COUNT} sample customers")
    print(f"Inserted {inserted_events} sample events")


if __name__ == "__main__":
    generate_events()