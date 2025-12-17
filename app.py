from flask import Flask, request, jsonify
import config
import psycopg2
from location import (
    get_location_by_address,
    process_location_data,
    find_nearest_volunteers_postgis, process_location_data,
    get_location_by_address
)
from config import DEFAULT_RADIUS_KM

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(config)


# --------------------------------------------------------
# API — UPDATE USER LOCATION
# --------------------------------------------------------

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


# --------------------------------------------------------
# API — FIND NEAREST VOLUNTEERS
# --------------------------------------------------------
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

if __name__ == '__main__':
    app.run(debug=True)



