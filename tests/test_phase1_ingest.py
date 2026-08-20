import pytest
import json
from unittest.mock import patch, MagicMock
from ingest_function.main import ingest_event


class TestIngestFunction:
    """Tests for Phase 1 ingest endpoint"""

    def create_request(self, method="POST", json_data=None):
        """Helper to create a mock request"""
        request = MagicMock()
        request.method = method
        request.get_json = MagicMock(return_value=json_data)
        return request

    @patch("ingest_function.main.pubsub_v1.PublisherClient")
    def test_ingest_valid_event_returns_202(self, mock_publisher_class):
        """Test that valid events return 202 Accepted"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher
        mock_future = MagicMock()
        mock_publisher.publish.return_value = mock_future

        request = self.create_request(json_data={
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z",
            "value": 99.99
        })

        response, status_code = ingest_event(request)

        assert status_code == 202
        assert response.json["status"] == "queued"

    def test_ingest_missing_customer_id_returns_400(self):
        """Test that missing customer_id returns 400"""
        request = self.create_request(json_data={
            "event_type": "view",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        })

        response, status_code = ingest_event(request)

        assert status_code == 400
        assert "customer_id" in response.json["error"]

    def test_ingest_invalid_event_type_returns_400(self):
        """Test that invalid event_type returns 400"""
        request = self.create_request(json_data={
            "event_type": "invalid_type",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        })

        response, status_code = ingest_event(request)

        assert status_code == 400
        assert "event_type" in response.json["error"]

    def test_ingest_purchase_without_value_returns_400(self):
        """Test that purchase events without value return 400"""
        request = self.create_request(json_data={
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        })

        response, status_code = ingest_event(request)

        assert status_code == 400
        assert "value" in response.json["error"]

    def test_ingest_invalid_method_returns_405(self):
        """Test that non-POST requests return 405"""
        request = self.create_request(method="GET")

        response, status_code = ingest_event(request)

        assert status_code == 405

    def test_ingest_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400"""
        request = self.create_request(json_data=None)

        response, status_code = ingest_event(request)

        assert status_code == 400

    def test_ingest_invalid_timestamp_returns_400(self):
        """Test that invalid timestamp returns 400"""
        request = self.create_request(json_data={
            "event_type": "view",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "not-a-timestamp"
        })

        response, status_code = ingest_event(request)

        assert status_code == 400
        assert "timestamp" in response.json["error"]

    @patch("ingest_function.main.pubsub_v1.PublisherClient")
    def test_ingest_pubsub_failure_returns_503(self, mock_publisher_class):
        """Test that Pub/Sub errors return 503"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Pub/Sub error")
        mock_publisher.publish.return_value = mock_future

        request = self.create_request(json_data={
            "event_type": "view",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        })

        response, status_code = ingest_event(request)

        assert status_code == 503
