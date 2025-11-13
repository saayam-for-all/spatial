"""
Contains all SQL queries and helper functions related to database operations.
"""

# ==============================
# SQL Queries
# ==============================

# Query to insert volunteer location data
INSERT_VOLUNTEER_LOCATION = """
INSERT INTO virginia_dev_saayam_rdbms.volunteer_locations (
    user_id, curr_loc
)
VALUES (
    %s, ST_GeogFromText(%s)
);
"""

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
