import pytest
from app import app
from unittest.mock import patch


# =========================================================
# FIXTURE: Flask Test Client
# =========================================================
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# =========================================================
# TESTS — UPDATE VOLUNTEER LOCATION
# =========================================================

# TC1: Valid GPS Input
@patch("app.process_location_data")
def test_update_location_valid_gps(mock_process, client):
    mock_process.return_value = {
        "latitude": 37.7749,
        "longitude": -122.4194
    }

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 37.7749,
        "longitude": -122.4194
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Location updated successfully"
    assert data["data"]["latitude"] == 37.7749


# TC2: Valid Address Input (Mock external API)
@patch("app.get_location_by_address")
@patch("app.process_location_data")
def test_update_location_with_address(mock_process, mock_geo, client):
    mock_geo.return_value = (40.7128, -74.0060, None)
    mock_process.return_value = {
        "latitude": 40.7128,
        "longitude": -74.0060
    }

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "address": "New York"
    })

    assert response.status_code == 200


# TC3: Missing user_id
def test_update_location_missing_user_id(client):
    response = client.post('/updateVolunteerLocation', json={
        "latitude": 37.7749,
        "longitude": -122.4194
    })

    assert response.status_code == 400
    assert "SAAYAM-10002" in response.get_json()["error"]


# TC4: Missing lat/lon AND address
def test_update_location_missing_coordinates(client):
    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123"
    })

    assert response.status_code == 400
    assert "SAAYAM-10004" in response.get_json()["error"]


# TC5: Invalid JSON
def test_update_location_invalid_json(client):
    response = client.post(
        '/updateVolunteerLocation',
        data="invalid_json",
        content_type="application/json"
    )

    assert response.status_code == 400


# TC6: Invalid Lat/Lon Type
def test_update_location_invalid_type(client):
    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": "abc",
        "longitude": -122.4194
    })

    assert response.status_code == 400
    assert "SAAYAM-10006" in response.get_json()["error"]


# TC7: Invalid Coordinate Range
def test_update_location_invalid_range(client):
    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 200,
        "longitude": 500
    })

    assert response.status_code == 400
    assert "SAAYAM-10007" in response.get_json()["error"]


# TC8: Address Not Found
@patch("app.get_location_by_address")
def test_update_location_invalid_address(mock_geo, client):
    mock_geo.return_value = (None, None, None)

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "address": "invalid_place_123"
    })

    assert response.status_code == 400
    assert "SAAYAM-10003" in response.get_json()["error"]


# TC9: Both GPS and Address (GPS should take priority)
@patch("app.process_location_data")
def test_update_location_gps_priority(mock_process, client):
    mock_process.return_value = {
        "latitude": 12.9716,
        "longitude": 77.5946
    }

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "address": "New York"
    })

    assert response.status_code == 200


# TC10: Edge Case (0,0)
@patch("app.process_location_data")
def test_update_location_zero_coordinates(mock_process, client):
    mock_process.return_value = {
        "latitude": 0,
        "longitude": 0
    }

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 0,
        "longitude": 0
    })

    assert response.status_code == 200


# TC11: Simulate DB Failure
@patch("app.process_location_data")
def test_update_location_db_failure(mock_process, client):
    mock_process.side_effect = Exception("DB error")

    response = client.post('/updateVolunteerLocation', json={
        "user_id": "user123",
        "latitude": 37.7749,
        "longitude": -122.4194
    })

    assert response.status_code == 500
    assert "SAAYAM-10500" in response.get_json()["error"]


# =========================================================
# TESTS — FIND NEARBY VOLUNTEERS
# =========================================================

from unittest.mock import patch


#  TC1: Basic valid request
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_basic(mock_db, client):
    mock_db.return_value = [{"user_id": "user1"}]

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37.7749,
        "longitude": -122.4194
    })

    assert response.status_code == 200
    assert "volunteers" in response.get_json()


#  TC2: Radius in KM
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_radius_km(mock_db, client):
    mock_db.return_value = []

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122,
        "radius": 10,
        "unit": "km"
    })

    assert response.status_code == 200


#  TC3: Radius in Miles (conversion check)
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_radius_miles(mock_db, client):
    mock_db.return_value = []

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122,
        "radius": 10,
        "unit": "miles"
    })

    assert response.status_code == 200


#  TC4: Legacy radius_km
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_legacy_radius(mock_db, client):
    mock_db.return_value = []

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122,
        "radius_km": 15
    })

    assert response.status_code == 200


#  TC5: Calamity mode (override radius)
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_calamity(mock_db, client):
    mock_db.return_value = []

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122,
        "is_calamity": True
    })

    assert response.status_code == 200


#  TC6: Limit parameter
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_limit(mock_db, client):
    mock_db.return_value = [{"user_id": "user1"}]

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122,
        "limit": 5
    })

    assert response.status_code == 200


#  TC7: Missing latitude/longitude
def test_find_volunteers_missing_lat_lon(client):
    response = client.post('/findNearbyVolunteers', json={
        "radius": 10
    })

    assert response.status_code == 400
    assert "SAAYAM-10004" in response.get_json()["error"]


#  TC8: Invalid JSON
def test_find_volunteers_invalid_json(client):
    response = client.post(
        '/findNearbyVolunteers',
        data="invalid_json",
        content_type="application/json"
    )

    assert response.status_code == 400


#  TC9: DB failure
@patch("app.find_nearest_volunteers_postgis")
def test_find_volunteers_db_failure(mock_db, client):
    mock_db.side_effect = Exception("DB error")

    response = client.post('/findNearbyVolunteers', json={
        "latitude": 37,
        "longitude": -122
    })

    assert response.status_code == 500
    assert "SAAYAM-10502" in response.get_json()["error"]