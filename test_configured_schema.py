"""Focused tests for the configured volunteer-location INSERT schema."""

import importlib

import psycopg2
import pytest
from psycopg2 import sql
from unittest.mock import MagicMock, patch

import config
import location
from app import app
from sql_query import (
    VOLUNTEER_LOCATIONS_TABLE,
    build_insert_volunteer_location_sql,
    get_geography_point,
    validate_schema_identifier,
)

DEFAULT_SCHEMA = "virginia_dev_saayam_rdbms"


def _statement_parts(query):
    """Split a composed statement into SQL text and identifier tuples."""
    assert isinstance(query, sql.Composed)
    sql_text = []
    identifiers = []
    for part in query.seq:
        if isinstance(part, sql.SQL):
            sql_text.append(part.string)
        elif isinstance(part, sql.Identifier):
            identifiers.append(part.strings)
        else:
            raise AssertionError(f"unexpected SQL part: {part!r}")
    return "".join(sql_text), identifiers


@pytest.fixture
def client():
    with app.test_client() as test_client:
        yield test_client


def test_default_schema_targets_historical_table(monkeypatch):
    monkeypatch.delenv("DB_SCHEMA", raising=False)
    original_schema = config.SCHEMA
    try:
        importlib.reload(config)
        assert config.SCHEMA == DEFAULT_SCHEMA

        sql_text, identifiers = _statement_parts(build_insert_volunteer_location_sql())
    finally:
        config.SCHEMA = original_schema

    assert identifiers == [(DEFAULT_SCHEMA, VOLUNTEER_LOCATIONS_TABLE)]
    assert "ST_GeogFromText(%s)" in sql_text
    assert sql_text.count("%s") == 2
    assert DEFAULT_SCHEMA not in sql_text


def test_custom_schema_is_read_when_the_statement_is_built(monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "staging_schema")

    sql_text, identifiers = _statement_parts(build_insert_volunteer_location_sql())

    assert identifiers == [("staging_schema", VOLUNTEER_LOCATIONS_TABLE)]
    assert "staging_schema" not in sql_text


def test_explicit_schema_argument_overrides_configured_schema(monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "staging_schema")

    _, identifiers = _statement_parts(
        build_insert_volunteer_location_sql("analytics_schema")
    )

    assert identifiers == [("analytics_schema", VOLUNTEER_LOCATIONS_TABLE)]


@pytest.mark.parametrize(
    "schema",
    [
        None,
        "",
        " ",
        "1schema",
        "virginia_dev_saayam_rdbms.volunteer_locations",
        'virginia"; DROP SCHEMA public; --',
        "schema name",
        "schema-name",
        'schema"',
        "schema'",
        "schema;drop",
        "schema\npublic",
        "a" * 64,
        "public.users",
        "schema$",
        b"public",
        12,
    ],
)
def test_unsafe_schema_inputs_are_rejected(schema):
    with pytest.raises(ValueError, match="Invalid database schema identifier"):
        validate_schema_identifier(schema)

    if schema is None:
        return

    with pytest.raises(ValueError, match="Invalid database schema identifier"):
        build_insert_volunteer_location_sql(schema)


def test_schema_at_identifier_length_limit_is_accepted():
    schema_name = "a" * 63

    _, identifiers = _statement_parts(build_insert_volunteer_location_sql(schema_name))

    assert identifiers == [(schema_name, VOLUNTEER_LOCATIONS_TABLE)]


def test_keyword_schema_stays_an_identifier():
    sql_text, identifiers = _statement_parts(build_insert_volunteer_location_sql("select"))

    assert identifiers == [("select", VOLUNTEER_LOCATIONS_TABLE)]
    assert "from select" not in sql_text.lower()
    assert "select.volunteer_locations" not in sql_text


def test_identifier_is_not_string_concatenated():
    query = build_insert_volunteer_location_sql("custom_schema")
    identifier_parts = [part for part in query.seq if isinstance(part, sql.Identifier)]

    assert len(identifier_parts) == 1
    assert identifier_parts[0].strings == ("custom_schema", VOLUNTEER_LOCATIONS_TABLE)
    assert not any(isinstance(part, sql.Literal) for part in query.seq)


@patch("location.psycopg2.connect")
def test_user_id_and_location_stay_bound_parameters(mock_connect):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_connection
    user_id = "user'); DROP TABLE users;--"

    result = location.process_location_data(user_id, 37.7749, -122.4194, "2026-11-12T00:00:00Z")

    query, params = mock_cursor.execute.call_args.args
    sql_text, identifiers = _statement_parts(query)
    assert result == {"latitude": 37.7749, "longitude": -122.4194}
    assert identifiers == [(config.SCHEMA, VOLUNTEER_LOCATIONS_TABLE)]
    assert params == (user_id, get_geography_point(37.7749, -122.4194))
    assert user_id not in sql_text
    assert "DROP TABLE" not in sql_text
    assert sql_text.count("%s") == 2
    mock_connection.commit.assert_called_once()


@patch("location.psycopg2.connect")
def test_configured_schema_is_used_for_the_insert(mock_connect, monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "custom_schema")
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_connection

    location.process_location_data("user123", 10.0, 20.0, "2026-11-12T00:00:00Z")

    query, params = mock_cursor.execute.call_args.args
    _, identifiers = _statement_parts(query)
    assert identifiers == [("custom_schema", VOLUNTEER_LOCATIONS_TABLE)]
    assert params == ("user123", "SRID=4326;POINT(20.0 10.0)")


@patch("location.psycopg2.connect")
def test_unsafe_schema_is_rejected_before_connect(mock_connect, monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "bad; DROP SCHEMA public; --")

    with pytest.raises(ValueError, match="Invalid database schema identifier"):
        location.process_location_data("user123", 10.0, 20.0, "2026-11-12T00:00:00Z")

    mock_connect.assert_not_called()


@patch("location.psycopg2.connect")
def test_database_error_still_rolls_back_and_raises(mock_connect, monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "custom_schema")
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = psycopg2.Error("insert failed")
    mock_connection.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_connection

    with pytest.raises(psycopg2.Error):
        location.process_location_data("user123", 10.0, 20.0, "2026-11-12T00:00:00Z")

    query, _params = mock_cursor.execute.call_args.args
    _, identifiers = _statement_parts(query)
    assert identifiers == [("custom_schema", VOLUNTEER_LOCATIONS_TABLE)]
    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


@patch("location.psycopg2.connect")
def test_update_route_returns_500_for_unsafe_schema(mock_connect, client, monkeypatch):
    monkeypatch.setattr(config, "SCHEMA", "bad schema")

    response = client.post(
        "/updateVolunteerLocation",
        json={"user_id": "user123", "latitude": 37.7749, "longitude": -122.4194},
    )

    assert response.status_code == 500
    assert "SAAYAM-10500" in response.get_json()["error"]
    mock_connect.assert_not_called()
