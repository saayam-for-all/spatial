from flask import Flask, request, jsonify
import config
from datetime import datetime, timezone
from locations import (
    process_location_data,
    get_user_last_location,
    find_nearest_volunteers_postgis
)
from util import get_location_by_address, get_location_by_ip

app = Flask(__name__)
app.config.from_object(config)

# =======================================================
# TASK 1: Update Volunteer Location 
# URL: /updateVolunteerLocation
# Logic: Uses YOUR improved logic (PostGIS & Error Codes)
# =======================================================
@app.route('/updateVolunteerLocation', methods=['POST'])
def update_Volunteer_Location():
    """
    Process and store user location data.
    This supports the 'Update Location' button on the frontend.
    """
    if not request.is_json:
        return jsonify({config.KEY_ERROR: config.ERROR_INVALID_JSON}), 400
        
    data = request.get_json()
    user_id = data.get(config.KEY_USER_ID)
    address = data.get('address')
    use_current_location = data.get('use_current_location', False)

    if not user_id:
        return jsonify({config.KEY_ERROR: config.ERROR_USER_ID_REQUIRED}), 400

    # Robust logic to handle IP vs Address
    if use_current_location:
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)
    elif address:
        lat, lon, timestamp = get_location_by_address(request.remote_addr, address)
    else:
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)

    if lat is None or lon is None:
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_UNDETERMINED}), 400

    try:
        # Saves data to 'volunteer_locations' table in PostGIS format
        processed_data = process_location_data(user_id, lat, lon, timestamp)
        return jsonify({
            config.KEY_MESSAGE: "Location data processed",
            config.KEY_DATA: processed_data
        }), 200
    except Exception as e:
        print(f"Error processing location: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_PROCESS_FAILED}), 500


# =======================================================
# TASK 2: Find Nearest Volunteers
# URL: /nearest_volunteers
# =======================================================
@app.route('/nearest_volunteers', methods=['POST'])
def find_nearest_volunteers():
    """
    Find nearest available volunteers using PostGIS.
    Supports input in both Miles and Kilometers.
    """
    if not request.is_json:
        return jsonify({config.KEY_ERROR: config.ERROR_INVALID_JSON}), 400
        
    data = request.get_json()
    lat = data.get(config.KEY_LATITUDE)
    lon = data.get(config.KEY_LONGITUDE)
    
    if lat is None or lon is None:
        return jsonify({config.KEY_ERROR: config.ERROR_LAT_LON_REQUIRED}), 400

    try:
        # 1. Check for Calamity
        is_calamity = data.get(config.KEY_IS_CALAMITY, False)
        
        # 2. Determine Radius
        final_radius_km = config.DEFAULT_RADIUS_KM

        if is_calamity:
            final_radius_km = config.CALAMITY_RADIUS_KM
        else:
            # Handle Miles vs KM
            input_radius = data.get(config.KEY_RADIUS)
            input_unit = data.get(config.KEY_UNIT, config.UNIT_KM).lower()
            
            legacy_radius_km = data.get('radius_km')

            if legacy_radius_km is not None:
                final_radius_km = legacy_radius_km
            elif input_radius is not None:
                if input_unit == config.UNIT_MILES:
                    final_radius_km = input_radius / config.MILES_PER_KM
                else:
                    final_radius_km = input_radius

        limit = data.get('limit', config.DEFAULT_LIMIT)
        
        # 3. Query Database
        volunteers = find_nearest_volunteers_postgis(lat, lon, final_radius_km, limit)
        
        return jsonify({config.KEY_VOLUNTEERS: volunteers}), 200
        
    except Exception as e:
        print(f"Error finding volunteers: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_VOLUNTEERS_FIND_FAILED}), 500


# =======================================================
# DEBUGGING: Get User Location
# URL: /user_location/<user_id>
# =======================================================
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
            return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_NOT_FOUND}), 404
    except Exception as e:
        print(f"Error getting location: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_GET_FAILED}), 500


if __name__ == '__main__':
    app.run(debug=True)