import json

import pandas as pd
import pytest

from google.cloud.aiplatform.prediction import LocalModel

from prediction_container.app import create_app
from training_container.train import train_model


@pytest.fixture
def trained_model_path(tmp_path):
    rows = []

    for i in range(40):
        high_value = i >= 20

        if high_value:
            total_value = 300 + i * 10
            label = 1

        else:
            total_value = 20 + i * 5
            label = 0

        rows.append({
            "customer_id": f"customer_{i}",
            "total_events": 5 + i,
            "total_value": total_value,
            "purchase_count": 3 if high_value else 1,
            "view_count": 4,
            "cart_count": 2,
            "days_since_last_event": 3,
            "label_high_value": label,
        })

    training_file = (
        tmp_path
        / "training_data.csv"
    )

    model_dir = (
        tmp_path
        / "model"
    )

    pd.DataFrame(
        rows
    ).to_csv(
        training_file,
        index=False
    )

    train_model(
        training_file,
        model_dir
    )

    return (
        model_dir
        / "model.joblib"
    )


def test_health_check_returns_200_when_model_loaded(
    trained_model_path
):
    app = create_app(
        trained_model_path
    )

    client = app.test_client()

    response = client.get(
        "/health"
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.get_json()
        == {
            "status": "ready"
        }
    )


def test_predict_returns_expected_shape_for_valid_input(
    trained_model_path
):
    app = create_app(
        trained_model_path
    )

    client = app.test_client()

    response = client.post(
        "/predict",
        json={
            "instances": [
                {
                    "total_events": 12,
                    "total_value": 250.0,
                    "purchase_count": 2,
                    "view_count": 8,
                    "cart_count": 2,
                    "days_since_last_event": 3,
                }
            ]
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.get_json()

    assert (
        "predictions"
        in data
    )

    assert (
        len(
            data["predictions"]
        )
        == 1
    )

    prediction = (
        data["predictions"][0]
    )

    assert (
        "label_high_value"
        in prediction
    )

    assert (
        "probability"
        in prediction
    )

    assert (
        prediction[
            "label_high_value"
        ]
        in [0, 1]
    )

    assert (
        0
        <= prediction["probability"]
        <= 1
    )


def test_predict_known_input_gives_intuitively_correct_direction(
    trained_model_path
):
    app = create_app(
        trained_model_path
    )

    client = app.test_client()

    response = client.post(
        "/predict",
        json={
            "instances": [
                {
                    "total_events": 30,
                    "total_value": 900.0,
                    "purchase_count": 8,
                    "view_count": 10,
                    "cart_count": 5,
                    "days_since_last_event": 1,
                }
            ]
        },
    )

    assert (
        response.status_code
        == 200
    )

    prediction = (
        response
        .get_json()[
            "predictions"
        ][0]
    )

    assert (
        prediction[
            "label_high_value"
        ]
        == 1
    )

    assert (
        prediction[
            "probability"
        ]
        > 0.5
    )


def test_predict_rejects_malformed_input_with_clear_error(
    trained_model_path
):
    app = create_app(
        trained_model_path
    )

    client = app.test_client()

    response = client.post(
        "/predict",
        json={
            "instances": [
                {
                    "total_events": 10,
                    "total_value": 300,
                }
            ]
        },
    )

    assert (
        response.status_code
        == 400
    )

    data = response.get_json()

    assert (
        "error"
        in data
    )


def test_local_model_deploy_to_local_endpoint_succeeds():
    local_model = LocalModel(
        serving_container_image_uri=(
            "local-prediction:latest"
        ),
        serving_container_predict_route=(
            "/predict"
        ),
        serving_container_health_route=(
            "/health"
        ),
        serving_container_ports=[
            8080
        ],
    )

    with local_model.deploy_to_local_endpoint(
        host_port="8084",
        container_ready_timeout=120,
    ) as endpoint:

        health_response = (
            endpoint.run_health_check()
        )

        assert (
            health_response.status_code
            == 200
        )

        request_body = json.dumps({
            "instances": [
                {
                    "total_events": 20,
                    "total_value": 500.0,
                    "purchase_count": 4,
                    "view_count": 10,
                    "cart_count": 3,
                    "days_since_last_event": 2,
                }
            ]
        })

        predict_response = (
            endpoint.predict(
                request=request_body,
                headers={
                    "Content-Type":
                        "application/json"
                },
            )
        )

        assert (
            predict_response.status_code
            == 200
        )

        response_data = (
            predict_response.json()
        )

        assert (
            "predictions"
            in response_data
        )

        assert (
            len(
                response_data[
                    "predictions"
                ]
            )
            == 1
        )

        prediction = (
            response_data[
                "predictions"
            ][0]
        )

        assert (
            "label_high_value"
            in prediction
        )

        assert (
            "probability"
            in prediction
        )