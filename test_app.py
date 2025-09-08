import pytest
from flask import json
from app import app, db
from models import User, LocationRequest, Volunteer
from datetime import datetime, timezone
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def mock_get_location_by_ip():
    with patch('app.get_location_by_ip') as mock:
        mock.return_value = (40.7128, -74.0060, datetime.now(timezone.utc))
        yield mock

@pytest.fixture
def mock_get_location_by_address():
    with patch('app.get_location_by_address') as mock:
        mock.return_value = (51.5074, -0.1278, datetime.now(timezone.utc))
        yield mock

def test_01_capture_location_use_current_location(client, mock_get_location_by_ip):
    response = client.post('/location', json={
        'user_id': 1,
        'use_current_location': True
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'data' in data
    assert data['data']['latitude'] == 40.7128
    assert data['data']['longitude'] == -74.0060

def test_01_capture_location_with_address(client, mock_get_location_by_address):
    response = client.post('/location', json={
        'user_id': 1,
        'address': 'London'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'data' in data
    assert data['data']['latitude'] == 51.5074
    assert data['data']['longitude'] == -0.1278

def test_01_capture_location_invalid_data(client):
    response = client.post('/location', data='not json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_02_get_user_location(client):
    with app.app_context():
        user = User(id=1)
        db.session.add(user)
        location = LocationRequest(user_id=1, latitude=40.7128, longitude=-74.0060)
        db.session.add(location)
        db.session.commit()

    response = client.get('/user_location/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user_id'] == 1
    assert data['latitude'] == 40.7128
    assert data['longitude'] == -74.0060

def test_02_get_user_location_not_found(client):
    response = client.get('/user_location/999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

@patch('app.get_nearest_volunteers')
def test_03_find_nearest_volunteers(mock_get_nearest_volunteers, client):
    mock_get_nearest_volunteers.return_value = [
        {"id": 1, "distance": 1.5},
        {"id": 2, "distance": 2.0}
    ]
    response = client.post('/nearest_volunteers', json={
        'latitude': 40.7128,
        'longitude': -74.0060
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'volunteers' in data
    assert len(data['volunteers']) == 2

def test_03_find_nearest_volunteers_invalid_data(client):
    response = client.post('/nearest_volunteers', data='not json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data