import importlib
import sys
from unittest.mock import patch

import pytest

SENTINEL = "sentinel-xyz"


@pytest.fixture(autouse=True)
def _restore_modules():
    """Tests here reload config/location/app; restore the originals afterwards
    so other test files keep patching the same module objects."""
    saved = {n: sys.modules.get(n) for n in ("config", "location", "app")}
    yield
    for name, mod in saved.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod


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


# --- SP-W1-010: geocoder timeout and None guard ---

def _fresh_location():
    for name in ("config", "location"):
        sys.modules.pop(name, None)
    import location
    return location


def test_geocoder_none_address_makes_no_network_call():
    location = _fresh_location()
    with patch("location.requests.get") as mock_get:
        assert location.get_location_by_address(None) == (None, None, None)
        assert location.get_location_by_address("") == (None, None, None)
        assert location.get_location_by_address(123) == (None, None, None)
    mock_get.assert_not_called()


def test_geocoder_timeout_returns_none_tuple():
    import requests
    location = _fresh_location()
    with patch("location.requests.get", side_effect=requests.exceptions.Timeout):
        assert location.get_location_by_address("1 Main St") == (None, None, None)


def test_geocoder_passes_timeout_to_requests():
    location = _fresh_location()
    with patch("location.requests.get") as mock_get:
        mock_get.return_value.json.return_value = []
        location.get_location_by_address("1 Main St")
    assert mock_get.call_args.kwargs["timeout"] == location.config.GEOCODER_TIMEOUT_SECONDS


def test_route_returns_10003_when_geocode_times_out():
    import requests
    _fresh_location()
    sys.modules.pop("app", None)
    import app as app_module
    with patch("location.requests.get", side_effect=requests.exceptions.Timeout), \
         patch("app.process_location_data") as mock_process:
        resp = app_module.app.test_client().post(
            "/updateVolunteerLocation",
            json={"user_id": "u1", "address": "1 Main St"},
        )
    assert resp.status_code == 400
    assert "SAAYAM-10003" in resp.get_json()[app_module.config.KEY_ERROR]
    mock_process.assert_not_called()
