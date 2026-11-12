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
