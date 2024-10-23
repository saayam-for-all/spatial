from flask import Flask, request, jsonify
from extensions import db
import config
from location import (
    process_location_data,
    get_location_by_address,
    get_location_by_ip,
    get_user_last_location,
    get_nearest_volunteers,
    update_volunteer_availability
)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


@app.route('/location', methods=['POST'])
def put_user_location():
    """
    Process and store user location data.
    
    Expected JSON payload:
    {
        "user_id": int,
        "is_volunteer": bool,
        "availability": bool,
        "address": string,
        "use_current_location": bool
    }
    """
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id')
        is_volunteer = data.get('is_volunteer', False)
        availability = data.get('availability', False)
        address = data.get('address')
        use_current_location = data.get('use_current_location', False)

        # Determine location based on input preferences
        if use_current_location:
            lat, lon, timestamp = get_location_by_ip(request.remote_addr)
        elif address:
            lat, lon, timestamp = get_location_by_address(request.remote_addr, address)
        else:
            lat, lon, timestamp = get_location_by_ip(request.remote_addr)

        if lat is None or lon is None:
            return jsonify({"error": "Unable to determine location"}), 400

        try:
            processed_data = process_location_data(
                user_id, lat, lon, timestamp, is_volunteer, availability
            )
            return jsonify({
                "message": "Location data processed",
                "data": processed_data
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    
    return jsonify({"error": "Invalid data format, must be JSON"}), 400


@app.route('/user_location/<int:user_id>', methods=['GET'])
def get_user_location(user_id):
    """
    Retrieve the last known location for a specific user.
    
    Parameters:
        user_id (int): User identifier
    """
    location = get_user_last_location(user_id)
    if location:
        return jsonify(location), 200
    return jsonify({"error": "User location not found"}), 404


@app.route('/update_availability', methods=['POST'])
def update_availability():
    """
    Update volunteer availability status.
    
    Expected JSON payload:
    {
        "user_id": int,
        "availability": bool
    }
    """
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id')
        availability = data.get('availability', True)
        
        try:
            updated_data = update_volunteer_availability(user_id, availability)
            return jsonify({
                "message": "Data Updated",
                "data": updated_data
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
            
    return jsonify({"error": "Invalid data format, must be JSON"}), 400


@app.route('/nearest_volunteers', methods=['POST'])
def find_nearest_volunteers():
    """
    Find nearest available volunteers within specified radius.
    
    Expected JSON payload:
    {
        "latitude": float,
        "longitude": float,
        "limit": int,
        "min_radius": float,
        "max_radius": float,
        "exception_id": list[int]
    }
    """
    if request.is_json:
        data = request.get_json()
        exception_id_list = data.get('exception_id', [])
        exception_id_set = set(exception_id_list)
        lat = data.get('latitude')
        lon = data.get('longitude')
        limit = data.get('limit', config.DEFAULT_SEARCH_LIMIT)
        min_radius = data.get('min_radius', config.MIN_SEARCH_RADIUS_KM)
        max_radius = data.get('max_radius', config.MAX_SEARCH_RADIUS_KM)

        if lat is None or lon is None:
            return jsonify({
                "error": "Latitude and longitude are required"
            }), 400

        volunteers = get_nearest_volunteers(
            lat, lon, limit, min_radius, max_radius, exception_id_set
        )
        return jsonify({"volunteers": volunteers}), 200
        
    return jsonify({"error": "Invalid data format, must be JSON"}), 400


if __name__ == '__main__':
    app.run(debug=True)