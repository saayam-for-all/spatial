from flask import Flask, request, jsonify
import config
from datetime import datetime, timezone
# Import the functions we just defined in location.py
from location import (
    process_location_data,
    get_user_last_location,
    find_nearest_volunteers_postgis
)
# We can also import the geocoding helpers from util.py
from util import get_location_by_address, get_location_by_ip

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(config)

# --- Endpoint 1: Update Location (from put_user_location.py) ---
@app.route('/location', methods=['POST'])
def put_user_location():
    """
    Process and store user location data.
    """
    if not request.is_json:
        return jsonify({"error": "Invalid data format, must be JSON"}), 400
        
    data = request.get_json()
    user_id = data.get('user_id')
    address = data.get('address')
    use_current_location = data.get('use_current_location', False)

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Determine location
    if use_current_location:
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)
    elif address:
        lat, lon, timestamp = get_location_by_address(request.remote_addr, address)
    else:
        # Fallback to IP if no option is provided
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)

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
    except Exception as e:
        print(f"Error processing location: {e}")
        return jsonify({"error": "Failed to process location"}), 500

# --- Endpoint 2: Get Location (from get_user_location.py) ---
@app.route('/user_location/<user_id>', methods=['GET'])
def get_user_location(user_id):
    """
    Retrieve the last known location for a specific user.
    """
    try:
        location = get_user_last_location(user_id)
        if location:
            return jsonify(location), 200
        else:
            return jsonify({"error": "User location not found"}), 404
    except Exception as e:
        print(f"Error getting location: {e}")
        return jsonify({"error": "Failed to get location"}), 500

# --- Endpoint 3: Find Nearest (from find_nearest_volunteers.py) ---
@app.route('/nearest_volunteers', methods=['POST'])
def find_nearest_volunteers():
    """
    Find nearest available volunteers using PostGIS.
    """
    if not request.is_json:
        return jsonify({"error": "Invalid data format, must be JSON"}), 400
        
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    
    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        radius_km = data.get('radius_km', config.DEFAULT_RADIUS_KM)
        limit = data.get('limit', config.DEFAULT_LIMIT)
        
        volunteers = find_nearest_volunteers_postgis(lat, lon, radius_km, limit)
        
        return jsonify({"volunteers": volunteers}), 200
        
    except Exception as e:
        print(f"Error finding volunteers: {e}")
        return jsonify({"error": "Failed to find volunteers"}), 500

if __name__ == '__main__':
    app.run(debug=True)
