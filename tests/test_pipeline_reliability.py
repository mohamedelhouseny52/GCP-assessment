"""Tests for database connections and aggregation concurrency."""

from datetime import datetime
from unittest.mock import Mock

import pytest

import MySql.MySql as mysql_helper
import aggregate_function.main as aggregation


def test_mysql_insert_stores_utc_datetime(monkeypatch):
    cursor = Mock()
    connection = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(mysql_helper, "get_connection", lambda: connection)

    mysql_helper.insert_event(
        {
            "customer_id": "customer_1",
            "event_type": "purchase",
            "product_id": "product_1",
            "value": 49.99,
            "timestamp": "2026-08-20T13:00:00+03:00",
        }
    )

    assert cursor.execute.call_args.args[1][-1] == datetime(2026, 8, 20, 10)
    connection.commit.assert_called_once_with()
    cursor.close.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_mysql_pool_reuses_connections(monkeypatch):
    pool = Mock()
    factory = Mock(return_value=pool)
    monkeypatch.setattr(mysql_helper, "MySQLConnectionPool", factory)
    mysql_helper.get_pool.cache_clear()

    try:
        mysql_helper.get_connection()
        mysql_helper.get_connection()
        factory.assert_called_once()
        assert pool.get_connection.call_count == 2
    finally:
        mysql_helper.get_pool.cache_clear()


def test_aggregation_uses_one_firestore_client_and_releases_lock(monkeypatch):
    cursor = Mock()
    cursor.fetchone.return_value = (1,)
    connection = Mock()
    connection.cursor.return_value = cursor
    db = Mock()
    client_factory = Mock(return_value=db)
    monkeypatch.setattr(aggregation, "get_connection", lambda: connection)
    monkeypatch.setattr(aggregation, "get_firestore_client", client_factory)
    monkeypatch.setattr(
        aggregation,
        "get_events",
        lambda: [
            {
                "customer_id": customer_id,
                "event_type": "view",
                "value": None,
                "event_timestamp": datetime(2026, 8, 20, 10),
            }
            for customer_id in ("customer_1", "customer_2")
        ],
    )

    aggregation.aggregate_customer_stats()

    client_factory.assert_called_once_with()
    assert db.collection.return_value.document.call_count == 2
    assert cursor.execute.call_count == 2
    assert "GET_LOCK" in cursor.execute.call_args_list[0].args[0]
    assert "RELEASE_LOCK" in cursor.execute.call_args_list[1].args[0]
    assert cursor.fetchone.call_count == 2
    connection.close.assert_called_once_with()


def test_aggregation_retries_when_lock_is_unavailable(monkeypatch):
    cursor = Mock()
    cursor.fetchone.return_value = (0,)
    connection = Mock()
    connection.cursor.return_value = cursor
    get_events = Mock()
    monkeypatch.setattr(aggregation, "get_connection", lambda: connection)
    monkeypatch.setattr(aggregation, "get_events", get_events)

    with pytest.raises(TimeoutError, match="aggregation lock"):
        aggregation.aggregate_customer_stats()

    get_events.assert_not_called()
    connection.close.assert_called_once_with()


def test_aggregation_releases_lock_when_read_fails(monkeypatch):
    cursor = Mock()
    cursor.fetchone.return_value = (1,)
    connection = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(aggregation, "get_connection", lambda: connection)
    monkeypatch.setattr(
        aggregation, "get_events", Mock(side_effect=RuntimeError("database read failed"))
    )

    with pytest.raises(RuntimeError, match="database read failed"):
        aggregation.aggregate_customer_stats()

    assert "RELEASE_LOCK" in cursor.execute.call_args.args[0]
    assert cursor.fetchone.call_count == 2
    connection.close.assert_called_once_with()
