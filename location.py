import requests
from urllib.parse import quote
from datetime import datetime, timezone
from util import lat_lon_to_tile_id, get_neighboring_tiles, calculate_distance

NOMINATIM_USER_AGENT = 'SaayamForAll/1.0 (info@saayam.com)'

def get_location_by_address(ip, address):
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    headers = {'User-Agent': NOMINATIM_USER_AGENT}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon']), datetime.now(timezone.utc)
        return get_location_by_ip(ip)
    except Exception as e:
        print(f"Error with address lookup: {e}")
        return get_location_by_ip(ip)

def get_location_by_ip(ip):
    url = f"https://ipapi.co/{ip}/json/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data['latitude']), float(data['longitude']), datetime.now(timezone.utc)
    except Exception as e:
        print(f"Error with IP lookup: {e}")
        return None, None, None