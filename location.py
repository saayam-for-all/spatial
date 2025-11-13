from datetime import datetime, timezone
import psycopg2
from config import db_config,NOMINATIM_USER_AGENT
from util import calculate_distance
from sql_file import INSERT_VOLUNTEER_LOCATION, get_geography_point

def process_location_data(user_id, lat, lon, timestamp):
    """
    Process and store user location data in the database.
    
    Args:
        user_id: Unique identifier for the user (string)
        lat: Latitude coordinate (float)
        lon: Longitude coordinate (float)
        timestamp: Time of location update
        
    Returns:
        dict: Contains processed location data
    """
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # Generate geospatial location string using helper
        curr_location = get_geography_point(lat, lon)

        # Execute insert query from sql_file.py
        cursor.execute(INSERT_VOLUNTEER_LOCATION, (user_id, curr_location))
        connection.commit()
        print("✅ Location update successful")

    except Exception as e:
        print("❌ Error while updating location:", e)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return {
        "latitude": lat,
        "longitude": lon
    }


def get_location_by_address(address):
    """
    Convert address to coordinates using Nominatim API.
    
    Args:
        address: Physical address to geocode
        
    Returns:
        tuple: (latitude, longitude, timestamp)
    """
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    headers = {'User-Agent': NOMINATIM_USER_AGENT}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon']), datetime.now(timezone.utc)
        else:
            print(f"No results found for address: {address}")
            return None, None, None
            
    except (requests.exceptions.RequestException, KeyError, ValueError, 
            IndexError, TypeError, AttributeError) as e:
        print(f"Error with location data: {e}")
        return None, None, None
