"""Train and save the Phase 5 scikit-learn model."""

import json
import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_SEED = 42
FEATURE_COLUMNS = [
    "total_events",
    "total_value",
    "purchase_count",
    "view_count",
    "cart_count",
    "days_since_last_event",
]
TARGET_COLUMN = "label_high_value"


def load_training_data(training_data_path):
    return pd.read_csv(training_data_path)


def split_features_and_target(data):
    return data[FEATURE_COLUMNS], data[TARGET_COLUMN]


def create_model():
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(random_state=RANDOM_SEED, max_iter=1000),
            ),
        ]
    )


def train_model(training_data_path, model_dir, random_seed=RANDOM_SEED):
    data = load_training_data(training_data_path)
    features, target = split_features_and_target(data)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=random_seed,
        stratify=target,
    )

    model = create_model()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "n_train": len(x_train),
        "n_test": len(x_test),
    }

    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")
    metrics_path = os.path.join(model_dir, "metrics.json")

    joblib.dump(model, model_path)
    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    return model, metrics


if __name__ == "__main__":
    train_model(
        os.getenv("TRAINING_DATA_PATH", "training_data.csv"),
        os.getenv("AIP_MODEL_DIR", "model_output"),
    )
