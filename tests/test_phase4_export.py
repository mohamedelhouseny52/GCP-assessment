import csv
from datetime import datetime

from export_job.main import (
    COLUMNS,
    prepare_training_rows,
    write_csv,
)


def test_export_produces_expected_columns(tmp_path):
    rows = [
        {
            "customer_id": "cust_1",
            "total_events": 3,
            "total_value": 250.0,
            "purchase_count": 1,
            "view_count": 1,
            "cart_count": 1,
            "last_event_at": datetime(2026, 9, 1),
        }
    ]

    now = datetime(2026, 9, 6)

    training_rows = prepare_training_rows(
        rows,
        now=now
    )

    output_file = tmp_path / "training_data.csv"

    write_csv(
        training_rows,
        output_file
    )

    with open(
        output_file,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.reader(file)
        header = next(reader)

    assert header == COLUMNS


def test_export_row_count_matches_distinct_customers():
    rows = [
        {
            "customer_id": "cust_1",
            "total_events": 3,
            "total_value": 250.0,
            "purchase_count": 1,
            "view_count": 1,
            "cart_count": 1,
            "last_event_at": datetime(2026, 9, 1),
        },
        {
            "customer_id": "cust_2",
            "total_events": 2,
            "total_value": 50.0,
            "purchase_count": 1,
            "view_count": 1,
            "cart_count": 0,
            "last_event_at": datetime(2026, 9, 2),
        },
    ]

    training_rows = prepare_training_rows(
        rows,
        now=datetime(2026, 9, 6)
    )

    assert len(training_rows) == 2


def test_export_label_matches_threshold_rule():
    rows = [
        {
            "customer_id": "high_value",
            "total_events": 3,
            "total_value": 250.0,
            "purchase_count": 2,
            "view_count": 1,
            "cart_count": 0,
            "last_event_at": datetime(2026, 9, 1),
        },
        {
            "customer_id": "low_value",
            "total_events": 2,
            "total_value": 100.0,
            "purchase_count": 1,
            "view_count": 1,
            "cart_count": 0,
            "last_event_at": datetime(2026, 9, 1),
        },
        {
            "customer_id": "exact_threshold",
            "total_events": 1,
            "total_value": 200.0,
            "purchase_count": 1,
            "view_count": 0,
            "cart_count": 0,
            "last_event_at": datetime(2026, 9, 1),
        },
    ]

    training_rows = prepare_training_rows(
        rows,
        now=datetime(2026, 9, 6)
    )

    result = {
        row["customer_id"]:
        row["label_high_value"]
        for row in training_rows
    }

    assert result["high_value"] == 1
    assert result["low_value"] == 0
    assert result["exact_threshold"] == 0


def test_export_handles_customer_with_zero_events():
    rows = []

    training_rows = prepare_training_rows(
        rows,
        now=datetime(2026, 9, 6)
    )

    assert training_rows == []


def test_export_no_null_values_in_output():
    rows = [
        {
            "customer_id": "cust_1",
            "total_events": 2,
            "total_value": 0,
            "purchase_count": 0,
            "view_count": 2,
            "cart_count": 0,
            "last_event_at": datetime(2026, 9, 1),
        }
    ]

    training_rows = prepare_training_rows(
        rows,
        now=datetime(2026, 9, 6)
    )

    for row in training_rows:
        for value in row.values():
            assert value is not None