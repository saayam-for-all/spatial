import requests
from urllib.parse import quote
from datetime import datetime, timezone

# Import configuration constants
import config 

# --- Geocoding Functions ---

def get_location_by_address(ip, address):
    """
    Convert address to coordinates using Nominatim API.
    Falls back to IP-based location on failure.
    """
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    headers = {'User-Agent': config.NOMINATIM_USER_AGENT} # Use constant from config
    
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
