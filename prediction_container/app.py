"""Small Vertex-style prediction server for the trained model."""

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


def resolve_model_path():
    storage_path = os.getenv("AIP_STORAGE_URI")
    if storage_path:
        return os.path.join(storage_path, "model.joblib")
    return os.getenv("MODEL_PATH", "/model/model.joblib")


def validate_instance(instance):
    if not isinstance(instance, dict):
        return "each instance must be a JSON object"

    for field in FEATURE_COLUMNS:
        if field not in instance:
            return f"missing required field: {field}"
        value = instance[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"field '{field}' must be numeric"

    return None


def create_app(model_path=None):
    app = Flask(__name__)
    model_path = model_path or resolve_model_path()

    try:
        model = joblib.load(model_path)
        print(f"Model loaded from: {model_path}", flush=True)
    except Exception as error:
        model = None
        print(f"Failed to load model: {error}", flush=True)

    @app.get("/health")
    def health():
        if model is None:
            return jsonify({"status": "not ready"}), 503
        return jsonify({"status": "ready"}), 200

    @app.post("/predict")
    def predict():
        if model is None:
            return jsonify({"error": "model is not loaded"}), 503

        body = request.get_json(silent=True)
        instances = body.get("instances") if isinstance(body, dict) else None
        if not isinstance(instances, list) or not instances:
            return jsonify({"error": "'instances' must be a non-empty list"}), 400

        for instance in instances:
            error = validate_instance(instance)
            if error:
                return jsonify({"error": error}), 400

        data = pd.DataFrame(instances, columns=FEATURE_COLUMNS)
        labels = model.predict(data)
        probabilities = model.predict_proba(data)[:, 1]
        predictions = [
            {
                "label_high_value": int(label),
                "probability": float(probability),
            }
            for label, probability in zip(labels, probabilities)
        ]
        return jsonify({"predictions": predictions}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
