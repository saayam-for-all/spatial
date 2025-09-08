# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///locations.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Tile system configuration
EARTH_RADIUS_KM = 6371  # Earth's radius in kilometers
S2_LEVEL = 5  # Size of each tile in s2 (6k cells for the whole world)

# Volunteer search configuration
DEFAULT_SEARCH_LIMIT = 5  # Default number of volunteers to return
MIN_SEARCH_RADIUS_KM = 0  # Minimum search radius in kilometers
MAX_SEARCH_RADIUS_KM = 1000  # Maximum search radius in kilometers

# Geolocation service configuration
NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'