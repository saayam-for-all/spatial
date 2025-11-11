import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
import config
from util import get_location_by_ip, get_location_by_address
import os # Import os to read the file

# --- Database Connection Helper ---

def get_db_connection():
    """Establishes a new database connection using settings from config.py."""
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )

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

# --- Logic for put_user_location ---

def process_location_data(user_id, lat, lon, timestamp):
    """
    Inserts or updates a user's location in the volunteer_locations table.
    """
    TABLE_VOL_LOCATIONS = config.TABLE_VOL_LOCATIONS
    
    sql = f"""
        INSERT INTO {TABLE_VOL_LOCATIONS} (user_id, curr_loc, updated_at)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET prev_loc = {TABLE_VOL_LOCATIONS}.curr_loc,
            curr_loc = EXCLUDED.curr_loc,
            updated_at = EXCLUDED.updated_at
        RETURNING user_id;
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, lon, lat, timestamp))
            conn.commit()
            
            result = cur.fetchone()
            if result:
                return {
                    config.KEY_USER_ID: result[0],
                    config.KEY_LATITUDE: lat,
                    config.KEY_LONGITUDE: lon,
                    config.KEY_TIMESTAMP: timestamp
                }
            else:
                raise Exception("Failed to insert or update location")
    finally:
        if conn:
            conn.close()

# --- Logic for get_user_location ---

def get_user_last_location(user_id):
    """
    Retrieves the last known location for a user.
    """
    TABLE_VOL_LOCATIONS = config.TABLE_VOL_LOCATIONS
    
    sql = f"""
        SELECT 
            ST_Y(curr_loc::geometry) AS {config.KEY_LATITUDE},
            ST_X(curr_loc::geometry) AS {config.KEY_LONGITUDE},
            updated_at AS last_update_date
        FROM {TABLE_VOL_LOCATIONS} 
        WHERE user_id = %s
    """
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_id,))
            location = cur.fetchone()
            if location:
                location[config.KEY_TIMESTAMP] = location['last_update_date'].isoformat()
                return location
            else:
                return None
    finally:
        if conn:
            conn.close()

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
                volunteers_list.append({
                    config.KEY_USER_ID: vol[config.KEY_USER_ID],
                    config.KEY_LOCATION: {
                        config.KEY_LATITUDE: vol[config.KEY_LATITUDE],
                        config.KEY_LONGITUDE: vol[config.KEY_LONGITUDE]
                    },
                    config.KEY_DISTANCE_KM: round(vol['distance_in_meters'] / 1000, 2)
                })
            return volunteers_list
    finally:
        if conn:
            conn.close()
