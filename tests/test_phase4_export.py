"""Tests for the Phase 4 training-data CSV."""

import csv
from datetime import datetime

from export_job.main import COLUMNS, prepare_training_rows, write_csv


def one_customer(total_value=250.0):
    return {
        "customer_id": "cust_1",
        "total_events": 3,
        "total_value": total_value,
        "purchase_count": 1,
        "view_count": 1,
        "cart_count": 1,
        "last_event_at": datetime(2026, 9, 1),
    }


def test_export_produces_expected_columns(tmp_path):
    rows = prepare_training_rows(
        [one_customer()],
        now=datetime(2026, 9, 6),
    )
    output_file = tmp_path / "training_data.csv"
    write_csv(rows, output_file)

    with open(output_file, newline="", encoding="utf-8") as file:
        header = next(csv.reader(file))

    assert header == COLUMNS


def test_export_row_count_matches_distinct_customers():
    first = one_customer(250.0)
    second = one_customer(50.0)
    second["customer_id"] = "cust_2"

    rows = prepare_training_rows(
        [first, second],
        now=datetime(2026, 9, 6),
    )

    assert len(rows) == 2


def test_export_label_matches_threshold_rule():
    high = one_customer(250.0)
    low = one_customer(100.0)
    exact = one_customer(200.0)
    low["customer_id"] = "low"
    exact["customer_id"] = "exact"

    rows = prepare_training_rows(
        [high, low, exact],
        now=datetime(2026, 9, 6),
    )
    labels = {row["customer_id"]: row["label_high_value"] for row in rows}

    assert labels["cust_1"] == 1
    assert labels["low"] == 0
    assert labels["exact"] == 0


def test_export_handles_no_customers():
    rows = prepare_training_rows([], now=datetime(2026, 9, 6))

    assert rows == []


def test_export_has_no_null_values():
    rows = prepare_training_rows(
        [one_customer(0)],
        now=datetime(2026, 9, 6),
    )

    for row in rows:
        assert all(value is not None for value in row.values())
