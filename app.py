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

@app.route('/location', methods=['POST'])
def put_user_location():
    """
    Process and store user location data.
    """
    if not request.is_json:
        # Use the new error code constant
        return jsonify({config.KEY_ERROR: config.ERROR_INVALID_JSON}), 400
        
    data = request.get_json()
    user_id = data.get(config.KEY_USER_ID)
    address = data.get('address')
    use_current_location = data.get('use_current_location', False)

    if not user_id:
        # Use the new error code constant
        return jsonify({config.KEY_ERROR: config.ERROR_USER_ID_REQUIRED}), 400

    if use_current_location:
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)
    elif address:
        lat, lon, timestamp = get_location_by_address(request.remote_addr, address)
    else:
        lat, lon, timestamp = get_location_by_ip(request.remote_addr)

    if lat is None or lon is None:
        # Use the new error code constant
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_UNDETERMINED}), 400

    try:
        processed_data = process_location_data(user_id, lat, lon, timestamp)
        return jsonify({
            config.KEY_MESSAGE: "Location data processed", # This could also be a SAAYAM-7xxx info code
            config.KEY_DATA: processed_data
        }), 200
    except Exception as e:
        print(f"Error processing location: {e}")
        # Use the new error code constant
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_PROCESS_FAILED}), 500

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
            # Use the new error code constant
            return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_NOT_FOUND}), 404
    except Exception as e:
        print(f"Error getting location: {e}")
        # Use the new error code constant
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_GET_FAILED}), 500

    
@app.route('/nearest_volunteers', methods=['POST'])
def find_nearest_volunteers():
    """
    Find nearest available volunteers using PostGIS.
    """
    if not request.is_json:
        return jsonify({config.KEY_ERROR: config.ERROR_INVALID_JSON}), 400

    data = request.get_json()
    lat = data.get(config.KEY_LATITUDE)
    lon = data.get(config.KEY_LONGITUDE)

    if lat is None or lon is None:
        return jsonify({config.KEY_ERROR: config.ERROR_LAT_LON_REQUIRED}), 400

    try:
        radius_km = data.get('radius_km', config.DEFAULT_RADIUS_KM)
        limit = data.get('limit', config.DEFAULT_LIMIT)

        volunteers = find_nearest_volunteers_postgis(lat, lon, radius_km, limit)

        sid_list = [v['user_id'] for v in volunteers]

        # If you only want one SID (the first one), use this:
        # return jsonify(sid_list[0]), 200

        # If you want all as a list:
        return jsonify(sid_list), 200

    except Exception as e:
        print(f"Error finding volunteers: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_VOLUNTEERS_FIND_FAILED}), 500


if __name__ == '__main__':
    app.run(debug=True)
