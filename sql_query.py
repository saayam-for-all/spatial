"""
Contains all SQL queries and helper functions related to database operations.
"""

import re

from psycopg2 import sql

import config

# Plain PostgreSQL identifiers only. Rejects quotes, dots, and SQL punctuation
# before the name is ever placed in a statement. 63 is NAMEDATALEN - 1.
_SCHEMA_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")

VOLUNTEER_LOCATIONS_TABLE = "volunteer_locations"

_INSERT_VOLUNTEER_LOCATION = sql.SQL(
    """
INSERT INTO {table} (
    user_id, curr_loc
)
VALUES (
    %s, ST_GeogFromText(%s)
);
"""
)


def validate_schema_identifier(schema):
    """
    Return schema when it is one plain PostgreSQL identifier.

    Raises:
        ValueError: schema is missing or is not a single unquoted identifier.
    """
    if not isinstance(schema, str) or _SCHEMA_IDENTIFIER.fullmatch(schema) is None:
        raise ValueError(
            "Invalid database schema identifier. "
            "DB_SCHEMA must be a single unquoted identifier: "
            "a letter or underscore, then letters, digits, or underscores, "
            "at most 63 characters."
        )
    return schema


def build_insert_volunteer_location_sql(schema=None):
    """
    Build the volunteer-location INSERT for the configured schema.

    The schema and table are sent as SQL identifiers. user_id and the
    geography text stay as bound parameters and are not interpolated.
    When schema is omitted, config.SCHEMA is used (DB_SCHEMA, or
    virginia_dev_saayam_rdbms when that variable is unset).
    """
    schema_name = config.SCHEMA if schema is None else schema
    validate_schema_identifier(schema_name)
    return _INSERT_VOLUNTEER_LOCATION.format(
        table=sql.Identifier(schema_name, VOLUNTEER_LOCATIONS_TABLE)
    )


# ==============================
# Helper Functions
# ==============================

def get_geography_point(lat, lon):
    """
    Returns a geography point string in WKT format with SRID=4326.

    Args:
        lat (float): Latitude
        lon (float): Longitude

    Returns:
        str: Geography point string formatted for PostgreSQL
    """
    return f"SRID=4326;POINT({lon} {lat})"
