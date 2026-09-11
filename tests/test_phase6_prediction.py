"""Tests for the Phase 6 prediction container."""

import json

import pandas as pd
import pytest
from google.cloud.aiplatform.prediction import LocalModel

from prediction_container.app import create_app
from training_container.train import train_model


def prediction_input(total_value=250.0):
    return {
        "total_events": 20,
        "total_value": total_value,
        "purchase_count": 4,
        "view_count": 10,
        "cart_count": 3,
        "days_since_last_event": 2,
    }


@pytest.fixture
def trained_model_path(tmp_path):
    rows = []
    for number in range(40):
        is_high_value = number >= 20
        if is_high_value:
            total_value = 300 + number * 10
            label = 1
            purchase_count = 3
        else:
            total_value = 20 + number * 5
            label = 0
            purchase_count = 1

        rows.append(
            {
                "customer_id": f"customer_{number}",
                "total_events": 5 + number,
                "total_value": total_value,
                "purchase_count": purchase_count,
                "view_count": 4,
                "cart_count": 2,
                "days_since_last_event": 3,
                "label_high_value": label,
            }
        )

    training_file = tmp_path / "training_data.csv"
    model_dir = tmp_path / "model"
    pd.DataFrame(rows).to_csv(training_file, index=False)
    train_model(training_file, model_dir)
    return model_dir / "model.joblib"


def test_health_check_returns_200_when_model_loaded(trained_model_path):
    client = create_app(trained_model_path).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_predict_returns_one_prediction(trained_model_path):
    client = create_app(trained_model_path).test_client()

    response = client.post(
        "/predict",
        json={"instances": [prediction_input()]},
    )
    prediction = response.get_json()["predictions"][0]

    assert response.status_code == 200
    assert prediction["label_high_value"] in [0, 1]
    assert 0 <= prediction["probability"] <= 1


def test_predict_high_value_input_returns_high_value_label(trained_model_path):
    client = create_app(trained_model_path).test_client()

    response = client.post(
        "/predict",
        json={"instances": [prediction_input(900.0)]},
    )
    prediction = response.get_json()["predictions"][0]

    assert response.status_code == 200
    assert prediction["label_high_value"] == 1
    assert prediction["probability"] > 0.5


def test_predict_rejects_missing_features(trained_model_path):
    client = create_app(trained_model_path).test_client()
    response = client.post(
        "/predict",
        json={"instances": [{"total_events": 10, "total_value": 300}]},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_local_model_deploys_checks_health_and_predicts():
    local_model = LocalModel(
        serving_container_image_uri="local-prediction:latest",
        serving_container_predict_route="/predict",
        serving_container_health_route="/health",
        serving_container_ports=[8080],
    )

    with local_model.deploy_to_local_endpoint(
        host_port="8084",
        container_ready_timeout=120,
    ) as endpoint:
        health_response = endpoint.run_health_check()
        assert health_response.status_code == 200

        request_body = json.dumps(
            {"instances": [prediction_input(500.0)]}
        )
        prediction_response = endpoint.predict(
            request=request_body,
            headers={"Content-Type": "application/json"},
        )

        assert prediction_response.status_code == 200
        predictions = prediction_response.json()["predictions"]
        assert len(predictions) == 1
        assert "label_high_value" in predictions[0]
        assert "probability" in predictions[0]
