import psycopg2
import psycopg2.extras
import config
from location import get_db_connection


def get_latest_location_from_db(user_id):
    """
    Fetch latest volunteer location from database.

    Args:
        user_id (str): Volunteer ID

    Returns:
        dict | None: Latest location info, or None if not found
    """
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = f"""
                SELECT 
                    user_id,
                    ST_Y(curr_loc::geometry) AS latitude,
                    ST_X(curr_loc::geometry) AS longitude,
                    updated_at
                FROM {config.TABLE_VOL_LOCATIONS}
                WHERE user_id = %s
                ORDER BY updated_at DESC
                LIMIT 1;
            """

            cur.execute(query, (user_id,))
            result = cur.fetchone()

            if not result:
                return None

            return {
                config.KEY_USER_ID: result["user_id"],
                config.KEY_LATITUDE: result["latitude"],
                config.KEY_LONGITUDE: result["longitude"],
                "last_updated": result["updated_at"].isoformat() if result["updated_at"] else None
            }

    except Exception as e:
        print(f"DB Error while fetching volunteer location: {e}")
        raise e

    finally:
        if conn:
            conn.close()