from datetime import datetime, timezone
from urllib.parse import quote
import requests
import psycopg2
from config import db_config,NOMINATIM_USER_AGENT
from util import calculate_distance


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
        curr_location = f"SRID=4326;POINT({lon} {lat})"
        # Use parameterized query to avoid SQL injection
        insert_query = f"""INSERT INTO virginia_dev_saayam_rdbms.volunteer_locations (
        user_id, curr_loc)
        VALUES ( %s,ST_GeogFromText(%s)
    ); """
        cursor.execute(insert_query,(user_id, curr_location))
        connection.commit()
        print("✅ Update successful")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return {
        "latitude": lat,
        "longitude": lon
    }


def get_location_by_address(ip, address):
    """
    Convert address to coordinates using Nominatim API.
    Falls back to IP-based location on failure.
    
    Args:
        ip: User's IP address for fallback
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
            print(f"Falling back to ip: {ip}")
            return get_location_by_ip(ip)
            
    except (requests.exceptions.RequestException, KeyError, ValueError, 
            IndexError, TypeError, AttributeError) as e:
        print(f"Error with location data: {e}")
        print(f"Falling back to ip: {ip}")
        return get_location_by_ip(ip)


def get_location_by_ip(ip):
    """
    Get location coordinates from IP address using ipapi.co.
    
    Args:
        ip: IP address to lookup
        
    Returns:
        tuple: (latitude, longitude, timestamp) or (None, None, None) on failure
    """
    
    url = f"https://ipapi.co/{ip}/json/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data['latitude']), float(data['longitude']), datetime.now(timezone.utc)
      
    except (requests.exceptions.RequestException, KeyError, ValueError, 
            TypeError, AttributeError) as e:
        print(f"Error with IP location data: {e}")
        return None, None, None
