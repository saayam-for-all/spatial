import pytest
from datetime import datetime, UTC, timezone
from urllib.parse import quote
import requests
import s2sphere
from location import (
    get_nearest_volunteers,
    get_location_by_address,
    get_location_by_ip
)
from util import (
    lat_lon_to_tile_id,
    tile_id_to_bounds,
    get_neighboring_tiles,
    calculate_distance
)
import config
from tabulate import tabulate
from flask import Flask
from extensions import db

@pytest.fixture
def mock_volunteer():
    class MockVolunteer:
        def __init__(self, id, lat, lon, last_login, availability, is_volunteer=True):
            self.id = id
            self.location_requests = [type('Request', (), {'latitude': lat, 'longitude': lon})]
            self.last_login = last_login
            self.volunteer = type('VolunteerInfo', (), {'availability': availability}) if is_volunteer else None
            self.is_volunteer = is_volunteer
            if lat is not None and lon is not None:
                self.tile_id = s2sphere.CellId.from_lat_lng(
                    s2sphere.LatLng.from_degrees(lat, lon)
                ).parent(config.S2_LEVEL).to_token()
            else:
                self.tile_id = None
    return MockVolunteer

@pytest.fixture
def sample_volunteers(mock_volunteer):
    current_time = datetime.now(UTC)
    return [
        mock_volunteer(1, 40.7128, -74.0060, current_time, True),  # NYC
        mock_volunteer(2, 40.7129, -74.0061, current_time, False), # NYC nearby
        mock_volunteer(3, 40.7130, -74.0062, current_time, True),  # NYC nearby
        mock_volunteer(4, 40.7131, -74.0063, current_time, True),  # NYC nearby
        mock_volunteer(5, 40.7132, -74.0064, current_time, False), # NYC nearby
        mock_volunteer(6, 34.0522, -118.2437, current_time, True), # Los Angeles
        mock_volunteer(7, 51.5074, -0.1278, current_time, True),   # London
        mock_volunteer(8, 35.6762, 139.6503, current_time, True),  # Tokyo
        mock_volunteer(9, 90.0, 0.0, current_time, True),          # North Pole
        mock_volunteer(10, -90.0, 0.0, current_time, True),        # South Pole
        mock_volunteer(11, 0.0, 179.9999, current_time, True),     # Date Line East
        mock_volunteer(12, 0.0, -179.9999, current_time, True)     # Date Line West
    ]

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def app_context(app):
    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

def test_01_volunteers_in_different_tiles(sample_volunteers):
    volunteers = sample_volunteers
    tile_ids = [v.tile_id for v in volunteers]
    
    print("\nTest 1: Volunteers in different tiles")
    table_data = [
        ["NYC volunteers in same tile", volunteers[0].tile_id == volunteers[1].tile_id],
        ["NY vs LA in different tiles", volunteers[0].tile_id != volunteers[5].tile_id],
        ["LA vs London in different tiles", volunteers[5].tile_id != volunteers[6].tile_id],
        ["London vs Tokyo in different tiles", volunteers[6].tile_id != volunteers[7].tile_id]
    ]
    print(tabulate(table_data, headers=["Test Case", "Result"]))
    
    assert volunteers[0].tile_id == volunteers[1].tile_id
    assert volunteers[0].tile_id != volunteers[5].tile_id
    assert volunteers[5].tile_id != volunteers[6].tile_id
    assert volunteers[6].tile_id != volunteers[7].tile_id


test_scenarios = [
    {
        "name": "normal_case",
        "search_lat": 40.7128,  # NYC
        "search_lon": -74.0060,
        "limit": 3,
        "min_radius": 0,
        "max_radius": 1,
        "exception_id": (),
        "expected_ids": [1, 3, 4]  # NYC area volunteers
    },
    {
        "name": "with_min_radius",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": 2,
        "max_radius": 10,
        "exception_id": (),
        "expected_ids": [6, 7]  # Should get LA and London
    },
    {
        "name": "unavailable_volunteers",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": 0,
        "max_radius": 1,
        "exception_id": (),
        "expected_ids": [1, 3, 4]  # Only available NYC volunteers
    },
    {
        "name": "no_volunteers_in_area",
        "search_lat": -45.0000,  # Middle of nowhere
        "search_lon": -45.0000,
        "limit": 5,
        "min_radius": 0,
        "max_radius": 1,
        "exception_id": (),
        "expected_ids": []
    },
    {
        "name": "volunteers_outside_radius",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 3,
        "min_radius": 6000,
        "max_radius": 7000,
        "exception_id": (),
        "expected_ids": [8]  # Only Tokyo in this range
    },
    {
        "name": "same_tile_search",
        "search_lat": 40.7128,  # NYC
        "search_lon": -74.0060,
        "limit": 3,
        "min_radius": 0,
        "max_radius": 1,
        "exception_id": (),
        "expected_ids": [1, 3, 4]
    },
    {
        "name": "cross_tile_search",
        "search_lat": 40.7128,  # NYC
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": 0,
        "max_radius": 5000,
        "exception_id": (),
        "expected_ids": [1, 3, 4, 6, 7]  # NYC, LA, and London
    },
    {
        "name": "global_search",
        "search_lat": 0.0,
        "search_lon": 0.0,
        "limit": 12,
        "min_radius": 0,
        "max_radius": 20000,
        "exception_id": (),
        "expected_ids": [1, 3, 4, 6, 7, 8, 9, 10, 11, 12]  # All available volunteers
    },
    {
        "name": "date_line_search",
        "search_lat": 0.0,
        "search_lon": 179.0,
        "limit": 2,
        "min_radius": 0,
        "max_radius": 1000,
        "exception_id": (),
        "expected_ids": [11, 12]  # Date line volunteers
    },
    {
        "name": "pole_search",
        "search_lat": 89.0,
        "search_lon": 0.0,
        "limit": 1,
        "min_radius": 0,
        "max_radius": 1000,
        "exception_id": (),
        "expected_ids": [9]  # North pole volunteer
    },
    {
        "name": "zero_radius_search",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": 0,
        "max_radius": 0,
        "exception_id": (),
        "expected_ids": [1]
    },
    {
        "name": "negative_radius",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": -10,
        "max_radius": -1,
        "exception_id": (),
        "expected_ids": []
    },
    {
        "name": "reversed_radius_bounds",
        "search_lat": 40.7128,
        "search_lon": -74.0060,
        "limit": 5,
        "min_radius": 10,
        "max_radius": 5,
        "exception_id": (),
        "expected_ids": []
    }
]
@pytest.mark.parametrize("scenario", test_scenarios, ids=[s["name"] for s in test_scenarios])
def test_02_get_nearest_volunteers_scenarios(app_context, sample_volunteers, monkeypatch, scenario):
    """Test scenarios with volunteers in verifiably different tiles."""
    class MockQuery:
        def __init__(self):
            self.filtered_volunteers = sample_volunteers
            self.volunteers = sample_volunteers

        def filter_by(self, **kwargs):
            self.filtered_volunteers = [
                user for user in self.volunteers 
                if all(getattr(user, key) == value for key, value in kwargs.items())
            ]
            return self

        def all(self):
            return self.filtered_volunteers

    class MockUser:
        query = MockQuery()

    monkeypatch.setattr('location.User', MockUser)
    monkeypatch.setattr('location.db.session.get', lambda model, id: None)

    result = get_nearest_volunteers(
        scenario["search_lat"],
        scenario["search_lon"],
        limit=scenario["limit"],
        min_radius=scenario["min_radius"],
        max_radius=scenario["max_radius"],
        exception_id=scenario["exception_id"],
    )

    result_ids = [v['id'] for v in result]
    is_correct = all(id in scenario["expected_ids"] for id in result_ids)
    
    table_data = [
        ["Scenario", scenario["name"]],
        ["Expected IDs", scenario["expected_ids"]],
        ["Actual IDs", result_ids],
        ["Correct", is_correct]
    ]
    print(f"\nTest 2: Get nearest volunteers scenario - {scenario['name']}")
    print(tabulate(table_data, headers=["Attribute", "Value"]))

    assert is_correct, f"Scenario '{scenario['name']}' failed: Expected {scenario['expected_ids']}, got {result_ids}"

def test_03_lat_lon_tile_conversion():
    print("\nTest 3: Latitude/longitude to tile conversion")
    tile1 = lat_lon_to_tile_id(0, 0)
    tile2 = lat_lon_to_tile_id(0.001, 0.001)
    tile3 = lat_lon_to_tile_id(10, 10)
    
    table_data = [
        ["(0, 0) == (0.001, 0.001)", tile1 == tile2],
        ["(0, 0) != (10, 10)", tile1 != tile3]
    ]
    print(tabulate(table_data, headers=["Test Case", "Result"]))
    
    assert tile1 == tile2
    assert tile1 != tile3

def test_04_tile_bounds():
    print("\nTest 4: Tile bounds")
    tile_id = lat_lon_to_tile_id(0, 0)
    lat_min, lon_min, lat_max, lon_max = tile_id_to_bounds(tile_id)
    
    table_data = [
        ["Latitude range", f"{lat_min} to {lat_max}"],
        ["Longitude range", f"{lon_min} to {lon_max}"],
        ["lat_min < lat_max", lat_min < lat_max],
        ["lon_min < lon_max", lon_min < lon_max]
    ]
    print(tabulate(table_data, headers=["Attribute", "Value"]))
    
    assert lat_min < lat_max
    assert lon_min < lon_max
    assert isinstance(lat_min, float)
    assert isinstance(lon_min, float)

def test_05_neighboring_tiles():
    print("\nTest 5: Neighboring tiles")
    center_tile = lat_lon_to_tile_id(0, 0)
    neighbors = get_neighboring_tiles(center_tile)
    
    table_data = [
        ["Number of neighbors", len(neighbors)],
        ["Center tile not in neighbors", center_tile not in neighbors],
        ["All neighbors are strings", all(isinstance(n, str) for n in neighbors)]
    ]
    print(tabulate(table_data, headers=["Test Case", "Result"]))
    
    assert len(neighbors) > 0
    assert center_tile not in neighbors
    assert all(isinstance(n, str) for n in neighbors)

@pytest.mark.parametrize("coordinates,expected_distance", [
    ((0, 0, 1, 1), 157.2),
    ((0, 0, 0, 0), 0),
    ((90, 0, -90, 0), 20015.1),
])
def test_06_calculate_distance(coordinates, expected_distance):
    distance = calculate_distance(*coordinates)
    print(f"\nTest 6: Distance calculation for coordinates {coordinates}")
    table_data = [
        ["Expected distance", expected_distance],
        ["Calculated distance", distance],
        ["Difference", abs(distance - expected_distance)]
    ]
    print(tabulate(table_data, headers=["Attribute", "Value"]))
    assert abs(distance - expected_distance) < 0.1

@pytest.mark.parametrize("mock_response,address,expected,scenario", [
    (
        [{'lat': '51.5074', 'lon': '-0.1278'}],
        'London',
        (51.5074, -0.1278),
        "Valid address"
    ),
    (
        [],
        'NonexistentPlace',
        None,
        "Invalid address"
    ),
    (
        [{'lat': '40.7128', 'lon': '-74.0060'}],
        'New York',
        (40.7128, -74.0060),
        "Another valid address"
    ),
    (
        None,
        'Paris',
        None,
        "RequestException scenario"
    ),
    (
        [{}],
        'Berlin',
        None,
        "KeyError scenario"
    ),
])
def test_07_get_location_by_address(mock_response, address, expected, scenario, monkeypatch):
    def mock_get(*args, **kwargs):
        if mock_response is None:
            raise requests.exceptions.RequestException("Mocked RequestException")
        return type('Response', (), {
            'json': lambda: mock_response,
            'raise_for_status': lambda: None
        })

    monkeypatch.setattr('requests.get', mock_get)
    monkeypatch.setattr('location.get_location_by_ip', lambda ip: (0, 0, datetime.now(timezone.utc)))

    print(f"\nTest 7: Get location by address - Scenario: {scenario}")
    result = get_location_by_address('127.0.0.1', address)

    table_data = [
        ["Address", address],
        ["Expected", expected],
        ["Result", result[:2] if result else None],
        ["Timestamp returned", isinstance(result[2], datetime) if result else None],
    ]
    print(tabulate(table_data, headers=["Attribute", "Value"]))

    if expected:
        assert result is not None
        assert abs(result[0] - expected[0]) < 0.0001
        assert abs(result[1] - expected[1]) < 0.0001
        assert isinstance(result[2], datetime)
    else:
        assert result == (0, 0, result[2])  # Fallback to IP (mocked)

@pytest.mark.parametrize("mock_response,ip,expected,scenario", [
    (
        {'latitude': 51.5074, 'longitude': -0.1278},
        '8.8.8.8',
        (51.5074, -0.1278),
        "Valid IP"
    ),
    (
        {'latitude': 37.7749, 'longitude': -122.4194},
        '1.1.1.1',
        (37.7749, -122.4194),
        "Another valid IP"
    ),
    (
        None,
        '192.168.0.1',
        (None, None),
        "RequestException scenario"
    ),
    (
        {},
        '10.0.0.1',
        (None, None),
        "KeyError scenario"
    ),
    (
        {'latitude': 'invalid', 'longitude': 'invalid'},
        '172.16.0.1',
        (None, None),
        "ValueError scenario"
    ),
])
def test_08_get_location_by_ip(mock_response, ip, expected, scenario, monkeypatch):
    def mock_get(*args, **kwargs):
        if mock_response is None:
            raise requests.exceptions.RequestException("Mocked RequestException")
        return type('Response', (), {
            'json': lambda: mock_response,
            'raise_for_status': lambda: None
        })

    monkeypatch.setattr('requests.get', mock_get)

    print(f"\nTest 8: Get location by IP - Scenario: {scenario}")
    result = get_location_by_ip(ip)

    table_data = [
        ["IP Address", ip],
        ["Expected", expected],
        ["Result", result[:2] if result else (None, None)],
        ["Timestamp returned", isinstance(result[2], datetime) if result else None],
    ]
    print(tabulate(table_data, headers=["Attribute", "Value"]))

    if expected[0] is not None:
        assert result is not None
        assert abs(result[0] - expected[0]) < 0.0001
        assert abs(result[1] - expected[1]) < 0.0001
        assert isinstance(result[2], datetime)
    else:
        assert result == (None, None, None)

def test_09_get_location_integration(monkeypatch):
    def mock_get(*args, **kwargs):
        if 'nominatim.openstreetmap.org' in args[0]:
            return type('Response', (), {
                'json': lambda: [],
                'raise_for_status': lambda: None
            })
        elif 'ipapi.co' in args[0]:
            return type('Response', (), {
                'json': lambda: {'latitude': 42.0, 'longitude': -71.0},
                'raise_for_status': lambda: None
            })

    monkeypatch.setattr('requests.get', mock_get)

    print("\nTest 9: Get location by address with fallback to IP")
    result = get_location_by_address('192.168.1.1', 'InvalidAddress')

    table_data = [
        ["Address", 'InvalidAddress'],
        ["IP", '192.168.1.1'],
        ["Expected", (42.0, -71.0)],
        ["Result", result[:2]],
        ["Timestamp returned", isinstance(result[2], datetime)],
    ]
    print(tabulate(table_data, headers=["Attribute", "Value"]))

    assert result[0] == 42.0
    assert result[1] == -71.0
    assert isinstance(result[2], datetime)

if __name__ == "__main__":
    pytest.main([__file__])