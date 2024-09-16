from flask import Flask, request, jsonify
from extensions import db
from location import process_location_data

app = Flask(__name__)

app.config.from_object('config')
db.init_app(app)

@app.route('/location', methods=['POST'])
def capture_location():
    if request.is_json:
        data = request.get_json()
        processed_data = process_location_data(data)
        return jsonify({"message": "Location data processed", "data": processed_data}), 200
    else:
        return jsonify({"error": "Invalid data format, must be JSON"}), 400

if __name__ == '__main__':
    app.run(debug=True)