import importlib
import sys
from unittest.mock import patch

SENTINEL = "sentinel-xyz"


def test_importing_app_does_not_print_db_password(monkeypatch, capsys):
    monkeypatch.setenv("DB_PASSWORD", SENTINEL)
    for name in ("config", "location", "app"):
        sys.modules.pop(name, None)
    importlib.import_module("app")

    captured = capsys.readouterr()
    assert SENTINEL not in captured.out
    assert SENTINEL not in captured.err


def test_get_db_connection_does_not_print_db_config(monkeypatch, capsys):
    monkeypatch.setenv("DB_PASSWORD", SENTINEL)
    for name in ("config", "location"):
        sys.modules.pop(name, None)
    import location

    with patch("location.psycopg2.connect") as mock_connect:
        location.get_db_connection()

    mock_connect.assert_called_once()
    captured = capsys.readouterr()
    assert SENTINEL not in captured.out
    assert SENTINEL not in captured.err


# --- SP-W2-002: validate /findNearbyVolunteers inputs ---

import pytest

_VALID = {"latitude": 37.7749, "longitude": -122.4194}


def _post_nearby(payload):
    import app as app_module
    with patch("app.find_nearest_volunteers_postgis", return_value=[]) as mock_db:
        resp = app_module.app.test_client().post("/findNearbyVolunteers", json=payload)
    return resp, mock_db, app_module.config


@pytest.mark.parametrize("extra, code", [
    ({"latitude": "37"}, "SAAYAM-10006"),
    ({"longitude": [1]}, "SAAYAM-10006"),
    ({"latitude": True}, "SAAYAM-10006"),
    ({"longitude": False}, "SAAYAM-10006"),
    ({"latitude": float("nan")}, "SAAYAM-10006"),
    ({"latitude": 91}, "SAAYAM-10007"),
    ({"latitude": -91}, "SAAYAM-10007"),
    ({"longitude": 181}, "SAAYAM-10007"),
    ({"longitude": -181}, "SAAYAM-10007"),
])
def test_nearby_rejects_bad_coordinates(extra, code):
    resp, mock_db, config = _post_nearby({**_VALID, **extra})
    assert resp.status_code == 400
    assert code in resp.get_json()[config.KEY_ERROR]
    mock_db.assert_not_called()


@pytest.mark.parametrize("extra", [
    {"radius": "10"},
    {"radius": True},
    {"radius": 0},
    {"radius": -5},
    {"radius": 1001},
    {"radius": 700, "unit": "miles"},   # ~1126 km after conversion
    {"radius_km": "10"},
    {"radius_km": 0},
    {"radius_km": 1001},
    {"radius_km": float("inf")},
    {"radius": 10, "unit": "miles", "radius_km": 5000},  # legacy wins
])
def test_nearby_rejects_bad_radius(extra):
    resp, mock_db, config = _post_nearby({**_VALID, **extra})
    assert resp.status_code == 400
    assert "SAAYAM-10009" in resp.get_json()[config.KEY_ERROR]
    mock_db.assert_not_called()


@pytest.mark.parametrize("limit", [0, -1, 51, 2.5, "5", True, None, [5]])
def test_nearby_rejects_bad_limit(limit):
    resp, mock_db, config = _post_nearby({**_VALID, "limit": limit})
    assert resp.status_code == 400
    assert "SAAYAM-10010" in resp.get_json()[config.KEY_ERROR]
    mock_db.assert_not_called()


@pytest.mark.parametrize("unit", ["meters", "", 5, None, True, ["km"]])
def test_nearby_rejects_bad_unit(unit):
    resp, mock_db, config = _post_nearby({**_VALID, "radius": 10, "unit": unit})
    assert resp.status_code == 400
    assert "SAAYAM-10011" in resp.get_json()[config.KEY_ERROR]
    mock_db.assert_not_called()


def test_nearby_rejects_non_object_json_body():
    import app as app_module
    with patch("app.find_nearest_volunteers_postgis") as mock_db:
        resp = app_module.app.test_client().post("/findNearbyVolunteers", json=[1, 2])
    assert resp.status_code == 400
    assert "SAAYAM-10001" in resp.get_json()[app_module.config.KEY_ERROR]
    mock_db.assert_not_called()


@pytest.mark.parametrize("extra, expected_km", [
    ({}, 25),
    ({"radius": 10, "unit": "km"}, 10),
    ({"radius": 10, "unit": "MILES"}, 10 / 0.621371),
    ({"radius_km": 15}, 15),
    ({"radius": 1000}, 1000),
    ({"is_calamity": True}, 200),
    ({"is_calamity": True, "radius": "ignored"}, 200),
])
def test_nearby_valid_requests_still_succeed(extra, expected_km):
    resp, mock_db, config = _post_nearby({**_VALID, **extra})
    assert resp.status_code == 200
    assert resp.get_json() == {"volunteers": []}
    lat, lon, radius_km, limit = mock_db.call_args.args
    assert radius_km == pytest.approx(expected_km)
    assert limit == config.DEFAULT_LIMIT


def test_nearby_limit_bounds_accepted():
    for limit in (1, 50):
        resp, mock_db, _ = _post_nearby({**_VALID, "limit": limit})
        assert resp.status_code == 200
        assert mock_db.call_args.args[3] == limit


# --- SP-W2-004: GET /getVolunteerLocation missing user_id ---

def test_get_volunteer_location_missing_user_id_uses_user_id_error():
    import app as app_module
    with patch("app.get_latest_location_from_db") as mock_db:
        resp = app_module.app.test_client().get("/getVolunteerLocation")
    assert resp.status_code == 400
    error = resp.get_json()[app_module.config.KEY_ERROR]
    assert error == app_module.config.ERROR_USER_ID_REQUIRED
    assert error.startswith("SAAYAM-10002")
    mock_db.assert_not_called()
