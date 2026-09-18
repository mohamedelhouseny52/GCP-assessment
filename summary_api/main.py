"""HTTP endpoint for one customer's Firestore summary."""

import os
from functools import lru_cache

from flask import jsonify
from google.cloud import firestore


REQUIRED_FIELDS = {
    "customer_id",
    "total_events",
    "total_value",
    "purchase_count",
    "last_event_at",
    "updated_at",
}


@lru_cache(maxsize=1)
def get_firestore_client():
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id and os.getenv("FIRESTORE_EMULATOR_HOST"):
        project_id = "local-project"
    return firestore.Client(project=project_id) if project_id else firestore.Client()


def get_customer_summary(customer_id):
    return (
        get_firestore_client()
        .collection("customer_aggregates")
        .document(customer_id)
        .get()
    )


def summary_api(request):
    """Handle GET /customers/{customer_id}/summary."""
    if request.method != "GET":
        return jsonify({"error": "method not allowed"}), 405

    path_parts = request.path.strip("/").split("/")
    correct_path = (
        len(path_parts) == 3
        and path_parts[0] == "customers"
        and path_parts[2] == "summary"
    )
    if not correct_path:
        return jsonify({"error": "not found"}), 404

    customer_id = path_parts[1]
    if not customer_id.strip() or len(customer_id) > 64:
        return jsonify({"error": "invalid customer_id"}), 400

    try:
        document = get_customer_summary(customer_id)
    except Exception:
        return jsonify({"error": "service unavailable"}), 503

    if not document.exists:
        return jsonify({"error": "customer not found"}), 404

    data = document.to_dict()
    if not REQUIRED_FIELDS.issubset(data):
        return jsonify({"error": "internal server error"}), 500

    return jsonify(data), 200
