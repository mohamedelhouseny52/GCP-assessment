from google.cloud import firestore
from flask import jsonify


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
    db = get_firestore_client()

    document = (
        db.collection("customer_aggregates")
        .document(customer_id)
        .get()
    )

    return document


def summary_api(request):

    if request.method != "GET":
        return jsonify({
            "error": "method not allowed"
        }), 405

    parts = request.path.strip("/").split("/")

    if (
        len(parts) != 3
        or parts[0] != "customers"
        or parts[2] != "summary"
    ):
        return jsonify({
            "error": "not found"
        }), 404

    customer_id = parts[1]

    try:
        document = get_customer_summary(customer_id)

    except Exception:
        print("Firestore is unreachable")

        return jsonify({
            "error": "service unavailable"
        }), 503

    if not document.exists:
        return jsonify({
            "error": "customer not found"
        }), 404

    data = document.to_dict()

    if not REQUIRED_FIELDS.issubset(data.keys()):
        print(
            f"Malformed document for customer: {customer_id}"
        )

        return jsonify({
            "error": "internal server error"
        }), 500

    return jsonify(data), 200