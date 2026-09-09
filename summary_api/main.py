"""HTTP endpoint for one customer's Firestore summary."""

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


def get_firestore_client():
    return firestore.Client(project="local-project")


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

    parts = request.path.strip("/").split("/")
    if len(parts) != 3 or parts[0] != "customers" or parts[2] != "summary":
        return jsonify({"error": "not found"}), 404

    try:
        document = get_customer_summary(parts[1])
    except Exception:
        return jsonify({"error": "service unavailable"}), 503

    if not document.exists:
        return jsonify({"error": "customer not found"}), 404

    data = document.to_dict()
    if not REQUIRED_FIELDS.issubset(data):
        return jsonify({"error": "internal server error"}), 500

    return jsonify(data), 200
