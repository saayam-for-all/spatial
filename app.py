from flask import Flask, request, jsonify
from datetime import datetime, timezone
import config
print("CONFIG FILE USED:", config.__file__)
print("DB CONFIG AT STARTUP:", config.db_config)
import psycopg2
from flask import request, jsonify
import psycopg2.extras
from location import (
    get_location_by_address,
    process_location_data,
    find_nearest_volunteers_postgis, process_location_data,
    get_location_by_address, get_db_connection
)
from dotenv import load_dotenv
load_dotenv()
from config import DEFAULT_RADIUS_KM

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(config)


# --------------------------------------------------------
# API — UPDATE VOLUNTEER LOCATION
# --------------------------------------------------------
@app.route('/updateVolunteerLocation', methods=['POST'])
def update_volunteer_location():
    """
    Supports BOTH:
    1. latitude & longitude (preferred)
    2. address (fallback)
    """

    # Validate JSON
    if not request.is_json:
        return jsonify({config.KEY_ERROR: config.ERROR_INVALID_JSON}), 400

    data = request.get_json()

    user_id = data.get('user_id')
    lat = data.get('latitude')
    lon = data.get('longitude')
    address = data.get('address')

    # Validate user_id
    if not user_id:
        return jsonify({config.KEY_ERROR: config.ERROR_USER_ID_REQUIRED}), 400
    
    # Default timestamp (always set)
    timestamp = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # PRIORITY 1: GPS (latitude & longitude)
    # --------------------------------------------------------
    if lat is not None and lon is not None:

        # Validate type
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return jsonify({config.KEY_ERROR: config.ERROR_INVALID_LAT_LON_TYPE}), 400

        # Validate range
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return jsonify({config.KEY_ERROR: config.ERROR_INVALID_COORDINATES}), 400
        

    # --------------------------------------------------------
    # PRIORITY 2: Address fallback
    # --------------------------------------------------------
    elif address:
        lat, lon, _ = get_location_by_address(address)

        if lat is None or lon is None:
            return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_UNDETERMINED}), 400

    # --------------------------------------------------------
    # INVALID INPUT
    # --------------------------------------------------------
    else:
        return jsonify({config.KEY_ERROR: config.ERROR_LAT_LON_REQUIRED}), 400

    # --------------------------------------------------------
    # STORE LOCATION
    # --------------------------------------------------------
    try:
        processed_data = process_location_data(user_id, lat, lon, timestamp)

        return jsonify({
            config.KEY_MESSAGE: "Location updated successfully",
            config.KEY_DATA: processed_data
        }), 200

    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_LOCATION_PROCESS_FAILED}), 500




# --------------------------------------------------------
# API — FIND NEAREST VOLUNTEERS
# --------------------------------------------------------
@app.route('/findNearbyVolunteers', methods=['POST'])
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
        # Check for the calamity flag
        is_calamity = data.get(config.KEY_IS_CALAMITY, False)
        
        # Initialize radius variable
        final_radius_km = config.DEFAULT_RADIUS_KM

        if is_calamity:
            final_radius_km = config.CALAMITY_RADIUS_KM
        else:
            # --- LOGIC TO HANDLE MILES VS KM ---
            
            # 1. Check for generic 'radius' and 'unit' (New Standard)
            input_radius = data.get(config.KEY_RADIUS)
            input_unit = data.get(config.KEY_UNIT, config.UNIT_KM).lower() # Default to KM
            
            # 2. Check for specific 'radius_km' (Backward Compatibility)
            # If 'radius_km' is explicitly sent, it takes precedence over the generic 'radius'
            legacy_radius_km = data.get('radius_km')

            if legacy_radius_km is not None:
                final_radius_km = legacy_radius_km
            elif input_radius is not None:
                if input_unit == config.UNIT_MILES:
                    # Convert Miles to Kilometers
                    # Formula: km = miles / 0.621371
                    final_radius_km = input_radius / config.MILES_PER_KM
                else:
                    # Assume KM
                    final_radius_km = input_radius
            
            # -----------------------------------

        limit = data.get('limit', config.DEFAULT_LIMIT)
        
        # The database function expects KM, so we pass the converted value
        volunteers = find_nearest_volunteers_postgis(lat, lon, final_radius_km, limit)
        
        return jsonify({config.KEY_VOLUNTEERS: volunteers}), 200
        
    except Exception as e:
        print(f"Error finding volunteers: {e}")
        return jsonify({config.KEY_ERROR: config.ERROR_VOLUNTEERS_FIND_FAILED}), 500

# --------------------------------------------------------
# API — GET VOLUNTEER LOCATION
# --------------------------------------------------------
from get_volunteer_location import get_latest_location_from_db

@app.route('/getVolunteerLocation', methods=['GET'])
def get_volunteer_location():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({
            config.KEY_ERROR: "SAAYAM-10004: user_id is required."
        }), 400

    try:
        result = get_latest_location_from_db(user_id)

        if not result:
            return jsonify({
                config.KEY_ERROR: config.ERROR_LOCATION_NOT_FOUND
            }), 404

        return jsonify(result), 200

    except Exception as e:
        print(f"Error fetching volunteer location: {e}")
        return jsonify({
            config.KEY_ERROR: config.ERROR_LOCATION_GET_FAILED
        }), 500
    
if __name__ == '__main__':
    app.run(debug=True)


