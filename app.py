from flask import Flask, request, jsonify
import config
from location import (
    process_location_data,
    get_location_by_address
)

import psycopg2
# Initialize Flask application
app = Flask(__name__)
app.config.from_object(config)

@app.route('/updateVolunteerLocation', methods=['POST'])
def update_Volunteer_Location():
    """
    Process and store user location data.
    
    Expected JSON payload:
    {
        "user_id": string,
        "address": string,
        "use_current_location": bool
    }
    """
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id')
        address = data.get('address')
        use_current_location = data.get('use_current_location', False)
        
        lat, lon, timestamp = get_location_by_address(address)

        if lat is None or lon is None:
            return jsonify({"error": "Unable to determine location"}), 400

        try:
            processed_data = process_location_data(
                user_id, lat, lon, timestamp
            )
            return jsonify({
                "message": "Location data processed",
                "data": processed_data
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    
    return jsonify({"error": "Invalid data format, must be JSON"}), 400

