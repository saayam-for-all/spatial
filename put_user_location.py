import json
import psycopg2
from util import lat_lon_to_tile_id, get_location_by_ip, get_location_by_address
from config import get_db_config

def get_db_connection():
    return psycopg2.connect(**get_db_config())

def lambda_handler(event, context):
    if event['httpMethod'] != 'POST':
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {"Content-Type": "application/json"}
        }

    try:
        data = json.loads(event['body'])
        user_id = data.get('user_id')
        is_volunteer = data.get('is_volunteer', False)
        availability = data.get('availability', False)
        address = data.get('address')
        use_current_location = data.get('use_current_location', False)
        ip = event['requestContext']['identity']['sourceIp']

        # Determine location
        if use_current_location:
            lat, lon, timestamp = get_location_by_ip(ip)
        elif address:
            lat, lon, timestamp = get_location_by_address(ip, address)
        else:
            lat, lon, timestamp = get_location_by_ip(ip)

        if lat is None or lon is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Unable to determine location"}),
                "headers": {"Content-Type": "application/json"}
            }

        tile_id = lat_lon_to_tile_id(lat, lon)
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Insert or update user_location with tile_id
            cur.execute("""
                INSERT INTO user_location (latitude, longitude, last_update_date, tile_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_location_id) DO UPDATE
                SET latitude = %s, longitude = %s, last_update_date = %s, tile_id = %s
                RETURNING user_location_id
            """, (lat, lon, timestamp, tile_id, lat, lon, timestamp, tile_id))
            user_location_id = cur.fetchone()[0]

            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                cur.execute("""
                    INSERT INTO users (user_id, is_volunteer, user_location_id)
                    VALUES (%s, %s, %s)
                """, (user_id, is_volunteer, user_location_id))
            else:
                cur.execute("""
                    UPDATE users
                    SET is_volunteer = %s, user_location_id = %s
                    WHERE user_id = %s
                """, (is_volunteer, user_location_id, user_id))

            if is_volunteer:
                cur.execute("SELECT user_id FROM volunteer_details WHERE user_id = %s", (user_id,))
                volunteer = cur.fetchone()
                if not volunteer:
                    cur.execute("""
                        INSERT INTO volunteer_details (user_id, availability, terms_and_conditions)
                        VALUES (%s, %s, %s)
                    """, (user_id, availability, True))
                else:
                    cur.execute("""
                        UPDATE volunteer_details
                        SET availability = %s
                        WHERE user_id = %s
                    """, (availability, user_id))

            conn.commit()
            processed_data = {"latitude": lat, "longitude": lon, "timestamp": timestamp.isoformat(), "tile_id": tile_id}
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Location data processed", "data": processed_data}),
                "headers": {"Content-Type": "application/json"}
            }

        except Exception as e:
            conn.rollback()
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