import os

# --- Database Configuration for psycopg2 ---
DB_HOST = os.environ.get('DB_HOST', 'TBD')
DB_PORT = os.environ.get('DB_PORT', 5432)
DB_NAME = os.environ.get('DB_NAME', 'TBD')
DB_USER = os.environ.get('DB_USER', 'TBD')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'TBD')
SCHEMA = "TBD"

# --- Geolocation Service Configuration ---
NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'

# --- Volunteer Search Configuration ---
DEFAULT_RADIUS_KM = 25
DEFAULT_LIMIT = 10
