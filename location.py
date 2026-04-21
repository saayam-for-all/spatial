import os # Import os to read the file
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import config
import requests

from config import get_db_config, NOMINATIM_USER_AGENT
from urllib.parse import quote 
from util import calculate_distance
from sql_query import INSERT_VOLUNTEER_LOCATION, get_geography_point

def get_db_connection():
    """
    Create and return a new PostgreSQL connection using db_config.
    """
    return psycopg2.connect(**get_db_config())

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
        connection = psycopg2.connect(**get_db_config())
        cursor = connection.cursor()

        # Generate geospatial location string using helper
        curr_location = get_geography_point(lat, lon)

        # Execute insert query from sql_file.py
        cursor.execute(INSERT_VOLUNTEER_LOCATION, (user_id, curr_location))
        connection.commit()
        print("Location update successful")

    except Exception as e:
        print(" Error while updating location:", e)

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

# --- SQL Query Loader ---
def load_sql_query(file_name):
    """Loads a SQL query from the 'sql' directory."""
    # Gets the path to the directory this file is in
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(base_dir, file_name)
    try:
        with open(sql_file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: SQL file not found at {sql_file_path}")
        raise



# --- Logic for find_nearest_volunteers ---

# Load the query from the file ONCE when the module is imported
NEAREST_VOLUNTEER_SQL_TEMPLATE = load_sql_query(config.SQL_FILE_PATH)

def find_nearest_volunteers_postgis(lat, lon, radius_km, limit):
    """
    Finds nearest volunteers by loading and executing the external SQL file.
    """
    radius_in_meters = radius_km * 1000

    # Format the SQL query with the correct table names
    sql_query = NEAREST_VOLUNTEER_SQL_TEMPLATE.format(
        TABLE_USERS=config.TABLE_USERS,
        TABLE_VOL_DETAILS=config.TABLE_VOL_DETAILS,
        TABLE_VOL_LOCATIONS=config.TABLE_VOL_LOCATIONS
    )
    
    params = (lon, lat, lon, lat, radius_in_meters, limit)

    volunteers_list = []
    conn = None

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql_query, params)
            volunteers = cur.fetchall()

            for vol in volunteers:
                # --- MODIFIED SECTION ---
                # Only append the user_id to the list
                volunteers_list.append({
                    config.KEY_USER_ID: vol[config.KEY_USER_ID]
                })
                # ------------------------
                
            return volunteers_list
    finally:
        if conn:
            conn.close()




