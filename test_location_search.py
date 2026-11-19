import pytest
from unittest.mock import MagicMock, patch

import location


def create_mock_database(rows):
    """Create a mocked PostgreSQL connection and cursor."""
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = rows

    return connection, cursor


@patch("location.get_db_connection")
def test_find_nearest_volunteers_returns_user_ids(mock_get_db):
    connection, cursor = create_mock_database([
        {"user_id": "volunteer-1"},
        {"user_id": "volunteer-2"},
    ])
    mock_get_db.return_value = connection

    result = location.find_nearest_volunteers_postgis(
        37.7749, -122.4194, 5, 10
    )

    assert result == [
        {location.config.KEY_USER_ID: "volunteer-1"},
        {location.config.KEY_USER_ID: "volunteer-2"},
    ]

    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == (
        -122.4194,
        37.7749,
        -122.4194,
        37.7749,
        5000,
        10,
    )
    connection.close.assert_called_once()


@patch("location.get_db_connection")
def test_find_nearest_volunteers_returns_empty_list(mock_get_db):
    connection, cursor = create_mock_database([])
    mock_get_db.return_value = connection

    result = location.find_nearest_volunteers_postgis(
        37.7749, -122.4194, 5, 10
    )

    assert result == []
    cursor.execute.assert_called_once()
    connection.close.assert_called_once()


@patch("location.get_db_connection")
def test_find_nearest_volunteers_closes_connection_on_query_error(mock_get_db):
    connection, cursor = create_mock_database([])
    cursor.execute.side_effect = RuntimeError("Database query failed")
    mock_get_db.return_value = connection

    with pytest.raises(RuntimeError, match="Database query failed"):
        location.find_nearest_volunteers_postgis(
            37.7749, -122.4194, 5, 10
        )

    connection.close.assert_called_once()
