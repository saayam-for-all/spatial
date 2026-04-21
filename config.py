# Database configuration
import os
from aws_param_store import load_db_config

_db_config_cache = None


def get_db_config():
    global _db_config_cache
    if _db_config_cache is None:
        _db_config_cache = load_db_config()
    return _db_config_cache
# --- Schema & table names ---
SCHEMA = os.environ.get("DB_SCHEMA", "virginia_dev_saayam_rdbms")

TABLE_USERS = f"{SCHEMA}.users"
TABLE_VOL_DETAILS = f"{SCHEMA}.volunteer_details"
TABLE_VOL_LOCATIONS = f"{SCHEMA}.volunteer_locations"

# Geocoder user-agent (safe to keep a default)
NOMINATIM_USER_AGENT = os.environ.get("NOMINATIM_USER_AGENT", "saayam-app")

# --- Volunteer Search ---
DEFAULT_RADIUS_KM = 25
CALAMITY_RADIUS_KM = 200
DEFAULT_LIMIT = 10
SQL_FILE_PATH = "sql/find_nearest_volunteers.sql"
MILES_PER_KM = 0.621371

# Tile system configuration
EARTH_RADIUS_KM = 6371  # Earth's radius in kilometers
S2_LEVEL = 5  # Size of each tile in s2 (6k cells for the whole world)

# Volunteer search configuration
DEFAULT_SEARCH_LIMIT = 5  # Default number of volunteers to return
MIN_SEARCH_RADIUS_KM = 0  # Minimum search radius in kilometers
MAX_SEARCH_RADIUS_KM = 1000  # Maximum search radius in kilometers

# Geolocation service configuration
#NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'

# --- API Request Keys ---
KEY_RADIUS = "radius"          # <-- NEW (Generic radius)
KEY_UNIT = "unit"              # <-- NEW (Unit specifier)
UNIT_MILES = "miles"           # <-- NEW
UNIT_KM = "km"                 # <-- NEW

# --- API Response Keys ---
KEY_ERROR = "error"
KEY_MESSAGE = "message"
KEY_DATA = "data"
KEY_VOLUNTEERS = "volunteers"
KEY_USER_ID = "user_id"
KEY_LATITUDE = "latitude"
KEY_LONGITUDE = "longitude"
KEY_TIMESTAMP = "timestamp"
KEY_LOCATION = "location"
KEY_DISTANCE_KM = "distance_km"
KEY_DISTANCE_MILES = "distance_miles"   
KEY_IS_CALAMITY = "is_calamity"       


# ====================================================================
# --- NEW SAAYAM ERROR CODES (Volunteer Service: 10000-15000) ---
# ====================================================================

# --- Informational Messages (Not used in this API yet) ---
# Example: INFO_LOCATION_UPDATED = "SAAYAM-10000: Location data processed."

# --- Client Error Messages (4xx) ---
ERROR_INVALID_JSON = (
    "SAAYAM-10001: Invalid data format. "
    "The request body must be valid JSON. "
    "Please check your request syntax."
)

ERROR_USER_ID_REQUIRED = (
    "SAAYAM-10002: User ID is required. "
    "The 'user_id' field is missing from your request. "
    "Please include your 'user_id' and try again."
)

ERROR_LOCATION_UNDETERMINED = (
    "SAAYAM-10003: Unable to determine location. "
    "The provided address could not be found, and no IP location was available. "
    "Please check the address for typos or try using a different location."
)

ERROR_LAT_LON_REQUIRED = (
    "SAAYAM-10004: Latitude and longitude are required. "
    "The 'latitude' and 'longitude' fields are missing from your request. "
    "Please include coordinates and try again."
)

ERROR_LOCATION_NOT_FOUND = (
    "SAAYAM-10005: User location not found. "
    "The requested user_id does not have a location in our records. "
    "Please ensure the user_id is correct or update the user's location first."
)

ERROR_INVALID_LAT_LON_TYPE = (
    "SAAYAM-10006: Invalid coordinate type. "
    "Latitude and longitude must be numeric values. "
    "Please provide valid numbers."
)

ERROR_INVALID_COORDINATES = (
    "SAAYAM-10007: Invalid coordinate range. "
    "Latitude must be between -90 and 90 and longitude between -180 and 180. "
    "Please provide valid GPS coordinates."
)

ERROR_MISSING_LOCATION_INPUT = (
    "SAAYAM-10008: Missing location input. "
    "Provide either latitude/longitude or a valid address."
)


# --- Server Error Messages (5xx) ---
ERROR_LOCATION_PROCESS_FAILED = (
    "SAAYAM-10500: Failed to process location. "
    "An internal server error occurred while writing to the database. "
    "Please contact the backend team if this error persists."
)

ERROR_LOCATION_GET_FAILED = (
    "SAAYAM-10501: Failed to get location. "
    "An internal server error occurred while reading from the database. "
    "Please contact the backend team if this error persists."
)

ERROR_VOLUNTEERS_FIND_FAILED = (
    "SAAYAM-10502: Failed to find volunteers. "
    "An internal server error occurred while querying for volunteers. "
    "Please contact the backend team if this error persists."
)