import pytest
import psycopg2
from unittest.mock import patch, MagicMock

from app import app
import location


# =========================================================
# FIXTURE: Flask Test Client
# =========================================================
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# =========================================================
# TESTS — process_location_data (unit level)
# =========================================================

# TC1: Successful commit returns coordinates
@patch("location.psycopg2.connect")
def test_process_location_data_success(mock_connect):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_connection

    result = location.process_location_data("user123", 37.7749, -122.4194, "2026-11-05T00:00:00Z")

    assert result == {"latitude": 37.7749, "longitude": -122.4194}
    mock_connection.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


# TC2: cursor.execute raising psycopg2.Error -> function raises, rollback called
@patch("location.psycopg2.connect")
def test_process_location_data_execute_failure_rolls_back_and_raises(mock_connect):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = psycopg2.Error("insert failed")
    mock_connection.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_connection

    with pytest.raises(psycopg2.Error):
        location.process_location_data("user123", 37.7749, -122.4194, "2026-11-05T00:00:00Z")

    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


# TC3: connect raising -> function raises
@patch("location.psycopg2.connect")
def test_process_location_data_connect_failure_raises(mock_connect):
    mock_connect.side_effect = psycopg2.Error("could not connect")

    with pytest.raises(psycopg2.Error):
        location.process_location_data("user123", 37.7749, -122.4194, "2026-11-05T00:00:00Z")


# =========================================================
# TEST — Flask route level
# =========================================================

# TC4: mocked connect raises -> /updateVolunteerLocation returns 500 with SAAYAM-10500
@patch("location.psycopg2.connect")
def test_update_location_route_returns_500_on_db_failure(mock_connect, client):
    mock_connect.side_effect = psycopg2.Error("could not connect")

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 37.7749,
        "longitude": -122.4194
    })

    assert response.status_code == 500
    assert "SAAYAM-10500" in response.get_json()["error"]