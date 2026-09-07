import os

import joblib
import pandas as pd
from flask import Flask, jsonify, request


FEATURE_COLUMNS = [
    "total_events",
    "total_value",
    "purchase_count",
    "view_count",
    "cart_count",
    "days_since_last_event",
]


def load_model(model_path):
    return joblib.load(model_path)


def validate_instance(instance):
    if not isinstance(instance, dict):
        return "each instance must be a JSON object"

    for field in FEATURE_COLUMNS:
        if field not in instance:
            return f"missing required field: {field}"

        value = instance[field]

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float)
        ):
            return f"field '{field}' must be numeric"

    return None


def resolve_model_path():
    storage_uri = os.getenv(
        "AIP_STORAGE_URI"
    )

    if storage_uri:
        return os.path.join(
            storage_uri,
            "model.joblib"
        )

    return os.getenv(
        "MODEL_PATH",
        "/model/model.joblib"
    )


def create_app(model_path=None):
    app = Flask(__name__)

    if model_path is None:
        model_path = resolve_model_path()

    model = None

    try:
        model = load_model(
            model_path
        )

        print(
            f"Model loaded from: {model_path}"
        )

    except Exception as error:
        print(
            f"Failed to load model: {error}"
        )

    @app.get("/health")
    def health():
        if model is None:
            return jsonify({
                "status": "not ready"
            }), 503

        return jsonify({
            "status": "ready"
        }), 200

    @app.post("/predict")
    def predict():
        if model is None:
            return jsonify({
                "error": "model is not loaded"
            }), 503

        body = request.get_json(
            silent=True
        )

        if not isinstance(body, dict):
            return jsonify({
                "error":
                    "request body must be JSON"
            }), 400

        instances = body.get(
            "instances"
        )

        if not isinstance(
            instances,
            list
        ):
            return jsonify({
                "error":
                    "'instances' must be a list"
            }), 400

        if len(instances) == 0:
            return jsonify({
                "error":
                    "'instances' cannot be empty"
            }), 400

        for instance in instances:
            validation_error = (
                validate_instance(
                    instance
                )
            )

            if validation_error:
                return jsonify({
                    "error":
                        validation_error
                }), 400

        rows = []

        for instance in instances:
            rows.append({
                field:
                    instance[field]
                for field
                in FEATURE_COLUMNS
            })

        data = pd.DataFrame(
            rows,
            columns=FEATURE_COLUMNS
        )

        labels = model.predict(
            data
        )

        probabilities = (
            model.predict_proba(
                data
            )[:, 1]
        )

        predictions = []

        for label, probability in zip(
            labels,
            probabilities
        ):
            predictions.append({
                "label_high_value":
                    int(label),

                "probability":
                    float(probability),
            })

        return jsonify({
            "predictions":
                predictions
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )