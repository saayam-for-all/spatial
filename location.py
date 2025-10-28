import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
import config
from util import get_location_by_ip, get_location_by_address

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

# --- Logic for put_user_location ---

def process_location_data(user_id, lat, lon, timestamp):
    """
    Inserts or updates a user's location in the volunteer_locations table.
    This version uses the correct 'curr_loc', 'prev_loc', and 'updated_at' columns.
   
    """
    TABLE_VOL_LOCATIONS = f"{config.SCHEMA}.volunteer_locations"
    
    # This query updates prev_loc with the old curr_loc,
    # and sets curr_loc to the new coordinates.
    sql = f"""
        INSERT INTO {TABLE_VOL_LOCATIONS} (user_id, curr_loc, updated_at)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET prev_loc = {TABLE_VOL_LOCATIONS}.curr_loc, -- Move current to previous
            curr_loc = EXCLUDED.curr_loc,             -- Set new location
            updated_at = EXCLUDED.updated_at
        RETURNING user_id;
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # PostGIS uses (lon, lat) for ST_MakePoint
            cur.execute(sql, (user_id, lon, lat, timestamp))
            conn.commit()
            
            result = cur.fetchone()
            if result:
                # Return the data that app.py expects
                return {"user_id": result[0], "latitude": lat, "longitude": lon, "timestamp": timestamp}
            else:
                raise Exception("Failed to insert or update location")
    finally:
        if conn:
            conn.close()

# --- Logic for get_user_location ---

def get_user_last_location(user_id):
    """
    Retrieves the last known location for a user.
    This version reads from 'curr_loc' and extracts lat/lon.
   
    """
    TABLE_VOL_LOCATIONS = f"{config.SCHEMA}.volunteer_locations"
    
    # ST_Y gets latitude, ST_X gets longitude
    sql = f"""
        SELECT 
            ST_Y(curr_loc::geometry) AS latitude,
            ST_X(curr_loc::geometry) AS longitude,
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
                location['timestamp'] = location['last_update_date'].isoformat()
                return location
            else:
                return None
    finally:
        if conn:
            conn.close()

# --- Logic for find_nearest_volunteers ---

def find_nearest_volunteers_postgis(lat, lon, radius_km, limit):
    """
    Finds nearest volunteers using the correct 'curr_loc' column.
    ** This version does NOT check for user availability. **
    """
    TABLE_USERS = f"{config.SCHEMA}.users"
    TABLE_VOL_DETAILS = f"{config.SCHEMA}.volunteer_details"
    TABLE_VOL_LOCATIONS = f"{config.SCHEMA}.volunteer_locations"
    
    radius_in_meters = radius_km * 1000

    # This query joins users, volunteer_details, and volunteer_locations.
    # The join to user_availability has been removed.
    sql_query = f"""
        SELECT
            u.user_id,
            u.full_name,
            ST_Y(vl.curr_loc::geometry) AS latitude,
            ST_X(vl.curr_loc::geometry) AS longitude,
            ST_Distance(
                vl.curr_loc::geography, -- Use the correct column
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance_in_meters
        FROM
            {TABLE_USERS} AS u
        JOIN
            {TABLE_VOL_DETAILS} AS vd ON u.user_id = vd.user_id --
        JOIN
            {TABLE_VOL_LOCATIONS} AS vl ON u.user_id = vl.user_id --
        WHERE
            -- This is the main search filter
            ST_DWithin(
                vl.curr_loc::geography, -- Use the correct column
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
        ORDER BY
            distance_in_meters ASC
        LIMIT %s;
    """
    # Params: (lon, lat, lon, lat, radius_meters, limit)
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
                    "user_id": vol['user_id'],
                    "full_name": vol['full_name'],
                    "location": {
                        "latitude": vol['latitude'],
                        "longitude": vol['longitude']
                    },
                    "distance_km": round(vol['distance_in_meters'] / 1000, 2)
                })
            return volunteers_list
    finally:
        if conn:
            conn.close()
