import json

import joblib
import pandas as pd

from training_container.train import (
    FEATURE_COLUMNS,
    train_model,
)


def create_test_dataset(file_path):
    rows = []

    for i in range(20):
        high_value = i >= 10

        if high_value:
            total_value = 300 + (i * 10)
            label = 1
        else:
            total_value = 50 + (i * 5)
            label = 0

        rows.append({
            "customer_id": f"customer_{i}",
            "total_events": 5 + i,
            "total_value": total_value,
            "purchase_count": 1 + (i % 4),
            "view_count": 2 + (i % 5),
            "cart_count": i % 3,
            "days_since_last_event": i % 10,
            "label_high_value": label,
        })

    data = pd.DataFrame(rows)

    data.to_csv(
        file_path,
        index=False
    )


def test_training_produces_model_artifact(
    tmp_path
):
    training_file = (
        tmp_path / "training_data.csv"
    )

    model_dir = (
        tmp_path / "model"
    )

    create_test_dataset(
        training_file
    )

    train_model(
        training_file,
        model_dir
    )

    model_file = (
        model_dir / "model.joblib"
    )

    assert model_file.exists()


def test_training_produces_metrics_file_with_expected_keys(
    tmp_path
):
    training_file = (
        tmp_path / "training_data.csv"
    )

    model_dir = (
        tmp_path / "model"
    )

    create_test_dataset(
        training_file
    )

    train_model(
        training_file,
        model_dir
    )

    metrics_file = (
        model_dir / "metrics.json"
    )

    assert metrics_file.exists()

    with open(
        metrics_file,
        "r",
        encoding="utf-8"
    ) as file:

        metrics = json.load(file)

    expected_keys = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "n_train",
        "n_test",
    }

    assert set(
        metrics.keys()
    ) == expected_keys


def test_model_can_be_loaded_and_predicts_correct_shape(
    tmp_path
):
    training_file = (
        tmp_path / "training_data.csv"
    )

    model_dir = (
        tmp_path / "model"
    )

    create_test_dataset(
        training_file
    )

    train_model(
        training_file,
        model_dir
    )

    model = joblib.load(
        model_dir / "model.joblib"
    )

    sample = pd.DataFrame([
        {
            "total_events": 8,
            "total_value": 350.0,
            "purchase_count": 3,
            "view_count": 3,
            "cart_count": 2,
            "days_since_last_event": 4,
        }
    ])

    sample = sample[
        FEATURE_COLUMNS
    ]

    prediction = model.predict(
        sample
    )

    assert prediction.shape == (1,)

    assert prediction[0] in [
        0,
        1
    ]


def test_training_is_reproducible(
    tmp_path
):
    training_file = (
        tmp_path / "training_data.csv"
    )

    first_model_dir = (
        tmp_path / "model_1"
    )

    second_model_dir = (
        tmp_path / "model_2"
    )

    create_test_dataset(
        training_file
    )

    _, metrics_1 = train_model(
        training_file,
        first_model_dir,
        random_seed=42
    )

    _, metrics_2 = train_model(
        training_file,
        second_model_dir,
        random_seed=42
    )

    assert metrics_1 == metrics_2