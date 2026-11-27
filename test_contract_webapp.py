"""Client contract tests for POST /updateVolunteerLocation.

Verifies spatial accepts the exact payloads sent by:
  - webapp:    src/services/volunteerLocationTracker.js (GPS first, address fallback)
  - mobileapp: services/endpoints.json (same UPDATE_VOLUNTEER_LOCATION endpoint)

Both clients post to "v1/spatial/updateVolunteerLocation", which the API
gateway forwards to /updateVolunteerLocation. Hermetic: DB writes and
Nominatim geocoding are mocked.
"""
from unittest.mock import patch

import pytest

import app as app_module

# webapp: user_id is auth.user.userDbId; coords are rounded to 4 decimals
# (formatCoordinate) and sent as JSON numbers.
WEBAPP_GPS_PAYLOAD = {
    "user_id": "SAAYAM-USER-0001",
    "latitude": 47.6062,
    "longitude": -122.3321,
}

# webapp address fallback: "city, state, country, zip" from personalInfo.
WEBAPP_ADDRESS_PAYLOAD = {
    "user_id": "SAAYAM-USER-0001",
    "address": "Seattle, Washington, United States, 98101",
}


def _post(payload, *, geocode=None, content_type_json=True):
    client = app_module.app.test_client()
    stored = {"user_id": payload.get("user_id") if isinstance(payload, dict) else None}
    with patch("app.process_location_data", return_value=stored) as mock_store, \
         patch("app.get_location_by_address", return_value=geocode or (None, None, None)) as mock_geo:
        if content_type_json:
            resp = client.post("/updateVolunteerLocation", json=payload)
        else:
            resp = client.post("/updateVolunteerLocation", data="x=1")
    return resp, mock_store, mock_geo


def test_webapp_gps_payload_accepted():
    resp, store, geo = _post(WEBAPP_GPS_PAYLOAD)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body[app_module.config.KEY_MESSAGE] == "Location updated successfully"
    assert app_module.config.KEY_DATA in body
    geo.assert_not_called()  # GPS takes priority, no geocoding
    user_id, lat, lon, _ts = store.call_args.args
    assert (user_id, lat, lon) == ("SAAYAM-USER-0001", 47.6062, -122.3321)


def test_webapp_address_fallback_payload_accepted():
    resp, store, geo = _post(WEBAPP_ADDRESS_PAYLOAD, geocode=(47.6097, -122.3331, "Seattle"))

    assert resp.status_code == 200
    geo.assert_called_once_with(WEBAPP_ADDRESS_PAYLOAD["address"])
    user_id, lat, lon, _ts = store.call_args.args
    assert (user_id, lat, lon) == ("SAAYAM-USER-0001", 47.6097, -122.3331)


def test_gps_wins_when_both_gps_and_address_present():
    payload = {**WEBAPP_GPS_PAYLOAD, "address": "Somewhere else"}
    resp, store, geo = _post(payload)

    assert resp.status_code == 200
    geo.assert_not_called()


@pytest.mark.parametrize("lat, lon", [(0, 0), (90, 180), (-90, -180), (47, -122)])
def test_gps_payload_accepts_integers_and_boundaries(lat, lon):
    resp, store, _ = _post({"user_id": "u1", "latitude": lat, "longitude": lon})

    assert resp.status_code == 200
    store.assert_called_once()


def test_address_fallback_unresolvable_returns_400():
    resp, store, geo = _post(WEBAPP_ADDRESS_PAYLOAD, geocode=(None, None, None))

    assert resp.status_code == 400
    assert resp.get_json()[app_module.config.KEY_ERROR] == app_module.config.ERROR_LOCATION_UNDETERMINED
    store.assert_not_called()


def test_payload_without_location_rejected():
    resp, store, _ = _post({"user_id": "u1"})

    assert resp.status_code == 400
    assert resp.get_json()[app_module.config.KEY_ERROR] == app_module.config.ERROR_LAT_LON_REQUIRED
    store.assert_not_called()


def test_payload_without_user_id_rejected():
    resp, store, _ = _post({"latitude": 1.0, "longitude": 2.0})

    assert resp.status_code == 400
    assert resp.get_json()[app_module.config.KEY_ERROR] == app_module.config.ERROR_USER_ID_REQUIRED
    store.assert_not_called()


def test_db_failure_returns_500_with_error_code():
    client = app_module.app.test_client()
    with patch("app.process_location_data", side_effect=RuntimeError("db down")):
        resp = client.post("/updateVolunteerLocation", json=WEBAPP_GPS_PAYLOAD)

    assert resp.status_code == 500
    assert resp.get_json()[app_module.config.KEY_ERROR] == app_module.config.ERROR_LOCATION_PROCESS_FAILED
