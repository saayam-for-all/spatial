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
