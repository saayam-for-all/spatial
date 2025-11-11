import os

# --- Database Connection ---
DB_HOST = os.environ.get('DB_HOST', 'TBD')
DB_PORT = os.environ.get('DB_PORT', 5432)
DB_NAME = os.environ.get('DB_NAME', 'virginia_dev_saayam_rdbms')
DB_USER = os.environ.get('DB_USER', 'TBD')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'TBD')
SCHEMA = "virginia_dev_saayam_rdbms"

# --- Database Tables ---
TABLE_USERS = f"{SCHEMA}.users"
TABLE_VOL_DETAILS = f"{SCHEMA}.volunteer_details"
TABLE_VOL_LOCATIONS = f"{SCHEMA}.volunteer_locations"

# --- Geolocation ---
NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'

# --- Volunteer Search ---
DEFAULT_RADIUS_KM = 25
DEFAULT_LIMIT = 10
SQL_FILE_PATH = "sql/find_nearest_volunteers.sql"

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

# ====================================================================
# --- NEW SAAYAM ERROR CODES (Volunteer Service: 7000-7999) ---
# ====================================================================

# --- Informational Messages (Not used in this API yet) ---
# Example: INFO_LOCATION_UPDATED = "SAAYAM-7000: Location data processed."

# --- Client Error Messages (4xx) ---
ERROR_INVALID_JSON = (
    "SAAYAM-7001: Invalid data format. "
    "The request body must be valid JSON. "
    "Please check your request syntax."
)

ERROR_USER_ID_REQUIRED = (
    "SAAYAM-7002: User ID is required. "
    "The 'user_id' field is missing from your request. "
    "Please include your 'user_id' and try again."
)

ERROR_LOCATION_UNDETERMINED = (
    "SAAYAM-7003: Unable to determine location. "
    "The provided address could not be found, and no IP location was available. "
    "Please check the address for typos or try using a different location."
)

ERROR_LAT_LON_REQUIRED = (
    "SAAYAM-7004: Latitude and longitude are required. "
    "The 'latitude' and 'longitude' fields are missing from your request. "
    "Please include coordinates and try again."
)

ERROR_LOCATION_NOT_FOUND = (
    "SAAYAM-7005: User location not found. "
    "The requested user_id does not have a location in our records. "
    "Please ensure the user_id is correct or update the user's location first."
)

# --- Server Error Messages (5xx) ---
ERROR_LOCATION_PROCESS_FAILED = (
    "SAAYAM-7500: Failed to process location. "
    "An internal server error occurred while writing to the database. "
    "Please contact the backend team if this error persists."
)

ERROR_LOCATION_GET_FAILED = (
    "SAAYAM-7501: Failed to get location. "
    "An internal server error occurred while reading from the database. "
    "Please contact the backend team if this error persists."
)

ERROR_VOLUNTEERS_FIND_FAILED = (
    "SAAYAM-7502: Failed to find volunteers. "
    "An internal server error occurred while querying for volunteers. "
    "Please contact the backend team if this error persists."
)
