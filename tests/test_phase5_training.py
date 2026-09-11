"""Tests for the Phase 5 scikit-learn training job."""

import json

import joblib
import pandas as pd

from training_container.train import FEATURE_COLUMNS, train_model


def create_test_dataset(file_path):
    rows = []

    for number in range(20):
        is_high_value = number >= 10
        if is_high_value:
            total_value = 300 + number * 10
            label = 1
        else:
            total_value = 50 + number * 5
            label = 0

        rows.append(
            {
                "customer_id": f"customer_{number}",
                "total_events": 5 + number,
                "total_value": total_value,
                "purchase_count": 1 + number % 4,
                "view_count": 2 + number % 5,
                "cart_count": number % 3,
                "days_since_last_event": number % 10,
                "label_high_value": label,
            }
        )

    pd.DataFrame(rows).to_csv(file_path, index=False)


def train_test_model(tmp_path, name="model"):
    training_file = tmp_path / "training_data.csv"
    model_dir = tmp_path / name
    create_test_dataset(training_file)
    return train_model(training_file, model_dir)


def test_training_produces_model_artifact(tmp_path):
    train_test_model(tmp_path)

    assert (tmp_path / "model" / "model.joblib").exists()


def test_training_produces_metrics_file_with_expected_keys(tmp_path):
    train_test_model(tmp_path)

    with open(tmp_path / "model" / "metrics.json", encoding="utf-8") as file:
        metrics = json.load(file)

    assert set(metrics) == {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "n_train",
        "n_test",
    }


def test_model_can_be_loaded_and_predicts_one_result(tmp_path):
    train_test_model(tmp_path)
    model = joblib.load(tmp_path / "model" / "model.joblib")
    sample = pd.DataFrame(
        [
            {
                "total_events": 8,
                "total_value": 350.0,
                "purchase_count": 3,
                "view_count": 3,
                "cart_count": 2,
                "days_since_last_event": 4,
            }
        ]
    )

    prediction = model.predict(sample[FEATURE_COLUMNS])

    assert prediction.shape == (1,)
    assert prediction[0] in [0, 1]


def test_training_is_reproducible(tmp_path):
    _, first_metrics = train_test_model(tmp_path, "model_1")
    _, second_metrics = train_test_model(tmp_path, "model_2")

    assert first_metrics == second_metrics
