import json
import os
import psycopg2
from util import lat_lon_to_tile_id, get_neighboring_tiles, calculate_distance

DEFAULT_SEARCH_LIMIT = 5
MIN_SEARCH_RADIUS_KM = 0
MAX_SEARCH_RADIUS_KM = 1000

def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )

def lambda_handler(event, context):
    if event['httpMethod'] != 'POST':
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {"Content-Type": "application/json"}
        }

    try:
        data = json.loads(event['body'])
        lat = data.get('latitude')
        lon = data.get('longitude')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)
        min_radius = data.get('min_radius', MIN_SEARCH_RADIUS_KM)
        max_radius = data.get('max_radius', MAX_SEARCH_RADIUS_KM)
        exception_id_list = data.get('exception_id', [])
        exception_id_set = set(exception_id_list)

        if lat is None or lon is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Latitude and longitude are required"}),
                "headers": {"Content-Type": "application/json"}
            }

        center_tile_id = lat_lon_to_tile_id(lat, lon)
        tiles_to_search = [center_tile_id] + get_neighboring_tiles(center_tile_id)
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT u.user_id, ul.latitude, ul.longitude, ul.last_update_date, v.availability, ul.tile_id
                FROM users u
                JOIN user_location ul ON u.user_location_id = ul.user_location_id
                JOIN volunteer_details v ON u.user_id = v.user_id
                WHERE ul.tile_id IN %s AND u.is_volunteer = TRUE AND v.availability = TRUE
            """, (tuple(tiles_to_search),))
            volunteers = cur.fetchall()

            volunteer_list = []
            for vol in volunteers:
                user_id, latitude, longitude, last_update_date, availability, tile_id = vol
                if user_id in exception_id_set:
                    continue
                distance = calculate_distance(lat, lon, latitude, longitude)
                if min_radius <= distance <= max_radius:
                    volunteer_list.append({
                        "id": user_id,
                        "distance": distance,
                        "location": {"latitude": latitude, "longitude": longitude},
                        "last_login": last_update_date.isoformat(),
                        "tile_id": tile_id
                    })

            volunteer_list.sort(key=lambda v: v["distance"])
            result = volunteer_list[:limit]
            return {
                "statusCode": 200,
                "body": json.dumps({"volunteers": result}),
                "headers": {"Content-Type": "application/json"}
            }

        except Exception as e:
            raise e
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }