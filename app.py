from flask import Flask, request, jsonify
from extensions import db
import config
from location import process_location_data, get_location_by_address, get_location_by_ip, get_user_location
from models import User, LocationRequest
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

@app.route('/location', methods=['POST'])
def capture_location():
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id')
        address = data.get('address')
        use_current_location = data.get('use_current_location', False)

        if use_current_location:
            lat, lon = get_location_by_ip(request.remote_addr)
        elif address:
            lat, lon = get_location_by_address(request.remote_addr, address)
        else:
            lat, lon = get_location_by_ip(request.remote_addr)

        try:
            processed_data = process_location_data(user_id, lat, lon)
            return jsonify({"message": "Location data processed", "data": processed_data}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        return jsonify({"error": "Invalid data format, must be JSON"}), 400

@app.route('/user_location/<int:user_id>', methods=['GET'])
def get_user_loc(user_id):
    location = get_user_location(user_id)
    if location:
        return jsonify(location), 200
    else:
        return jsonify({"error": "User location not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)