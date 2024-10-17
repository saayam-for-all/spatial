from models import User, LocationRequest
from extensions import db
from datetime import datetime
import requests
import requests
from urllib.parse import quote

def process_location_data(user_id, lat, lon):
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)

    location_request = LocationRequest(
        user_id=user_id,
        latitude=lat,
        longitude=lon,
        timestamp=datetime.utcnow()
    )
    db.session.add(location_request)
    db.session.commit()

    # save_to_mbtiles(lat, lon)

    return {"latitude": lat, "longitude": lon}

def get_location_by_address(ip, address):
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    
    headers = {'User-Agent': 'SaayamForAll/1.0 (info@saayam.com)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon'])
        else:
            print(f"No results found for address: {address}")
            return get_location_by_ip(ip)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location data: {e}")
        return get_location_by_ip(ip)
    except (KeyError, ValueError, IndexError) as e:
        print(f"Error parsing location data: {e}")
        return get_location_by_ip(ip)

def get_location_by_ip(ip):
    url = f"https://ipapi.co/{ip}/json/"
    print("my ip is", ip)
    response = requests.get(url)
    data = response.json()
    print("my data is ", data)
    return data['latitude'], data['longitude']

def get_user_location(user_id):
    location = LocationRequest.query.filter_by(user_id=user_id).order_by(LocationRequest.timestamp.desc()).first()
    if location:
        return {
            "user_id": user_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": location.timestamp
        }
    return None

def save_to_mbtiles(lat, lon):
    # This is a placeholder function. Implementing a full MBTiles solution
    # requires more complex setup and is beyond the scope of this example.
    # You would typically use a tool like Mapbox Tilemill or tippecanoe
    # to generate MBTiles from your data.
    pass