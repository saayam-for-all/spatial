import os


SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URI",
    "postgresql://user:password@localhost:5432/saayam_local_db"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False


# --- Volunteer Search Configuration ---
DEFAULT_SEARCH_LIMIT = 5
MIN_SEARCH_RADIUS_KM = 0
MAX_SEARCH_RADIUS_KM = 1000


# --- Geolocation Service and Tile System Configuration ---
NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'
EARTH_RADIUS_KM = 6371  # Earth's radius in kilometers
S2_LEVEL = 5  # Size of each tile in s2 (6k cells for the whole world)


