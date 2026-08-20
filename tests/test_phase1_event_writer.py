import pytest
import json
from unittest.mock import patch, MagicMock
from event_writer.event_writer import event_writer, validation


class TestEventWriter:
    """Tests for Phase 1 event writer"""

    def create_pubsub_message(self, data):
        """Helper to create a mock Pub/Sub message"""
        event = {
            "data": json.dumps(data).encode("utf-8")
        }
        return event

    @patch("event_writer.event_writer.insert_event")
    def test_event_writer_processes_valid_message(self, mock_insert):
        """Test that valid Pub/Sub messages are processed"""
        event_data = {
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z",
            "value": 99.99
        }

        event = self.create_pubsub_message(event_data)
        event_writer(event, None)

        mock_insert.assert_called_once()
        call_args = mock_insert.call_args[0][0]
        assert call_args["customer_id"] == "cust_123"

    def test_event_writer_handles_malformed_pubsub_message(self):
        """Test that malformed messages are handled gracefully"""
        # Invalid JSON
        event = {"data": b"not valid json"}

        # Should not raise exception
        result = event_writer(event, None)
        assert result is None

    def test_event_writer_handles_missing_required_field(self):
        """Test that messages with missing fields are rejected"""
        event_data = {
            "event_type": "view",
            "customer_id": "cust_123",
            # Missing product_id
            "timestamp": "2026-08-20T10:15:00Z"
        }

        event = self.create_pubsub_message(event_data)

        # Should not raise exception
        result = event_writer(event, None)
        assert result is None


class TestValidation:
    """Tests for event validation logic"""

    def test_validation_accepts_valid_view_event(self):
        """Test that valid view events pass validation"""
        data = {
            "event_type": "view",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        # Should not raise
        validation(data)

    def test_validation_accepts_valid_add_to_cart_event(self):
        """Test that valid add_to_cart events pass validation"""
        data = {
            "event_type": "add_to_cart",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        # Should not raise
        validation(data)

    def test_validation_accepts_valid_purchase_event(self):
        """Test that valid purchase events with value pass validation"""
        data = {
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z",
            "value": 99.99
        }

        # Should not raise
        validation(data)

    def test_validation_rejects_non_dict(self):
        """Test that non-dict data is rejected"""
        with pytest.raises(ValueError):
            validation([1, 2, 3])

    def test_validation_rejects_missing_customer_id(self):
        """Test that missing customer_id is rejected"""
        data = {
            "event_type": "view",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_missing_event_type(self):
        """Test that missing event_type is rejected"""
        data = {
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_missing_product_id(self):
        """Test that missing product_id is rejected"""
        data = {
            "event_type": "view",
            "customer_id": "cust_123",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_missing_timestamp(self):
        """Test that missing timestamp is rejected"""
        data = {
            "event_type": "view",
            "customer_id": "cust_123",
            "product_id": "prod_456"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_invalid_event_type(self):
        """Test that invalid event_type is rejected"""
        data = {
            "event_type": "invalid",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_purchase_without_value(self):
        """Test that purchase events without value are rejected"""
        data = {
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_purchase_with_non_numeric_value(self):
        """Test that purchase events with non-numeric value are rejected"""
        data = {
            "event_type": "purchase",
            "customer_id": "cust_123",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z",
            "value": "not a number"
        }

        with pytest.raises(ValueError):
            validation(data)

    def test_validation_rejects_empty_customer_id(self):
        """Test that empty customer_id is rejected"""
        data = {
            "event_type": "view",
            "customer_id": "",
            "product_id": "prod_456",
            "timestamp": "2026-08-20T10:15:00Z"
        }

        with pytest.raises(ValueError):
            validation(data)
