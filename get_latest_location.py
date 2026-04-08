import json
import os
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )


def lambda_handler(event, context):
    if event['httpMethod'] != 'GET':
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {"Content-Type": "application/json"}
        }

    user_id = event['pathParameters']['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                ST_Y(curr_loc::geometry) AS latitude,
                ST_X(curr_loc::geometry) AS longitude,
                updated_at
            FROM virginia_dev_saayam_rdbms.volunteer_locations
            WHERE user_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,))
        location = cur.fetchone()
        if location:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "user_id": user_id,
                    "latitude": location[0],
                    "longitude": location[1],
                    "last_updated": location[2].isoformat()
                }),
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User location not found"}),
                "headers": {"Content-Type": "application/json"}
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
    finally:
        cur.close()
        conn.close()
