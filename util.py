import s2sphere
import math
import requests
from urllib.parse import quote
from datetime import datetime, timezone

# Import configuration constants
import config 

# --- S2 Tiling and Distance Functions (from your original util.py) ---

def lat_lon_to_tile_id(lat, lon):
    """
    Convert latitude and longitude coordinates to an S2 tile ID.
   
    """
    lat_lng = s2sphere.LatLng.from_degrees(lat, lon)
    cell = s2sphere.CellId.from_lat_lng(lat_lng).parent(config.S2_LEVEL)
    return cell.to_token()

def get_neighboring_tiles(tile_id):
    """
    Get the IDs of all adjacent tiles for a given tile.
   
    """
    cell = s2sphere.CellId.from_token(tile_id)
    neighbors = [n.to_token() for n in cell.get_all_neighbors(config.S2_LEVEL)]
    return neighbors

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points using the Haversine formula.
   
    """
    # Convert all coordinates to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula components
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return config.EARTH_RADIUS_KM * c

# --- Geocoding Functions (from your original location.py) ---

def get_location_by_address(ip, address):
    """
    Convert address to coordinates using Nominatim API.
    Falls back to IP-based location on failure.
   
    """
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    headers = {'User-Agent': config.NOMINATIM_USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon']), datetime.now(timezone.utc)
        else:
            print(f"No results found for address: {address}")
            print(f"Falling back to ip: {ip}")
            return get_location_by_ip(ip)
            
    except (requests.exceptions.RequestException, KeyError, ValueError, 
            IndexError, TypeError, AttributeError) as e:
        print(f"Error with location data: {e}")
        print(f"Falling back to ip: {ip}")
        return get_location_by_ip(ip)


def get_location_by_ip(ip):
    """
    Get location coordinates from IP address using ipapi.co.
   
    """
    # Use a real IP, 127.0.0.1 (localhost) will fail
    if ip == '127.0.0.1':
        ip = '8.8.8.8' # Google's DNS for testing
        
    url = f"https://ipapi.co/{ip}/json/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data['latitude']), float(data['longitude']), datetime.now(timezone.utc)
    except (requests.exceptions.RequestException, KeyError, ValueError, 
            TypeError, AttributeError) as e:
        print(f"Error with IP location data: {e}")
        return None, None, None
