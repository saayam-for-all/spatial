import os
import pytest
import psycopg2

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("SPATIAL_IT_DB_HOST"),
        reason="SPATIAL_IT_DB_HOST not set; skipping integration tests",
    ),
]

from location import process_location_data  # noqa: E402

TEST_USER_ID = "test-volunteer-sp-w2-001"


@pytest.fixture
def db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("SPATIAL_IT_DB_HOST", "localhost"),
        port=os.environ.get("SPATIAL_IT_DB_PORT", "5432"),
        dbname=os.environ.get("SPATIAL_IT_DB_NAME", "postgres"),
        user=os.environ.get("SPATIAL_IT_DB_USER", "postgres"),
        password=os.environ.get("SPATIAL_IT_DB_PASSWORD", "localonly"),
    )
    yield conn
    cursor = conn.cursor()
    for table in ("volunteer_locations", "volunteer_details", "users"):
        cursor.execute(
            f"DELETE FROM virginia_dev_saayam_rdbms.{table} WHERE user_id = %s;",
            (TEST_USER_ID,),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def seeded_volunteer(db_connection):
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO virginia_dev_saayam_rdbms.users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;",
        (TEST_USER_ID,),
    )
    cursor.execute(
        "INSERT INTO virginia_dev_saayam_rdbms.volunteer_details (user_id) VALUES (%s) ON CONFLICT DO NOTHING;",
        (TEST_USER_ID,),
    )
    db_connection.commit()
    return TEST_USER_ID


def test_first_write_inserts_row(db_connection, seeded_volunteer):
    lat, lon = 37.7749, -122.4194

    result = process_location_data(seeded_volunteer, lat, lon, "2026-11-11T12:00:00Z")
    assert result == {"latitude": lat, "longitude": lon}

    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT curr_loc, prev_loc FROM virginia_dev_saayam_rdbms.volunteer_locations WHERE user_id = %s;",
        (seeded_volunteer,),
    )
    row = cursor.fetchone()
    assert row is not None
    assert row[0] is not None
    assert row[1] is None  # no prior position yet


def test_second_write_shifts_location(db_connection, seeded_volunteer):
    lat1, lon1 = 37.7749, -122.4194
    lat2, lon2 = 34.0522, -118.2437

    process_location_data(seeded_volunteer, lat1, lon1, "2026-11-11T12:00:00Z")
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT updated_at FROM virginia_dev_saayam_rdbms.volunteer_locations WHERE user_id = %s;",
        (seeded_volunteer,),
    )
    first_updated_at = cursor.fetchone()[0]

    process_location_data(seeded_volunteer, lat2, lon2, "2026-11-11T12:30:00Z")

    cursor.execute(
        "SELECT ST_Y(curr_loc::geometry), ST_X(curr_loc::geometry), "
        "ST_Y(prev_loc::geometry), ST_X(prev_loc::geometry), updated_at "
        "FROM virginia_dev_saayam_rdbms.volunteer_locations WHERE user_id = %s;",
        (seeded_volunteer,),
    )
    curr_lat, curr_lon, prev_lat, prev_lon, second_updated_at = cursor.fetchone()

    assert curr_lat == pytest.approx(lat2, abs=1e-6)
    assert curr_lon == pytest.approx(lon2, abs=1e-6)
    assert prev_lat == pytest.approx(lat1, abs=1e-6)
    assert prev_lon == pytest.approx(lon1, abs=1e-6)
    assert second_updated_at > first_updated_at


def test_non_volunteer_raises_fk_violation(db_connection):
    invalid_user_id = "non-existent-user-sp-w2-001"
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        process_location_data(invalid_user_id, 30.0, -100.0, "2026-11-11T12:00:00Z")
    db_connection.rollback()