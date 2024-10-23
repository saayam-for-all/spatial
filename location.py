from models import User, LocationRequest, Volunteer
from extensions import db
from datetime import datetime, timezone
from urllib.parse import quote
import requests
from config import (
    DEFAULT_SEARCH_LIMIT,
    MIN_SEARCH_RADIUS_KM,
    MAX_SEARCH_RADIUS_KM,
    NOMINATIM_USER_AGENT
)
from util import lat_lon_to_tile_id, get_neighboring_tiles, calculate_distance


def process_location_data(user_id, lat, lon, timestamp, is_volunteer, availability):
    """
    Process and store user location data in the database.
    
    Args:
        user_id: Unique identifier for the user
        lat: Latitude coordinate
        lon: Longitude coordinate
        timestamp: Time of location update
        is_volunteer: Boolean indicating if user is a volunteer
        availability: Volunteer availability status
        
    Returns:
        dict: Contains processed location data
    """
    user = db.session.get(User, user_id)
    
    # Create new user if doesn't exist
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        if is_volunteer:
            volunteer = Volunteer(id=user_id, availability=availability)
            db.session.add(volunteer)
    else:
        # Update existing volunteer status
        if is_volunteer:
            volunteer = db.session.get(Volunteer, user_id)
            if not volunteer:
                volunteer = Volunteer(id=user_id, availability=availability)
                db.session.add(volunteer)
            else:
                volunteer.availability = availability

    # Update user location and status
    tile_id = lat_lon_to_tile_id(lat, lon)
    user.tile_id = tile_id
    user.last_login = timestamp
    user.is_volunteer = is_volunteer
    
    # Record location request
    location_request = LocationRequest(
        user_id=user_id,
        latitude=lat,
        longitude=lon,
        timestamp=timestamp
    )
    db.session.add(location_request)
    db.session.commit()
    
    return {
        "latitude": lat,
        "longitude": lon,
        "timestamp": user.last_login
    }


def get_location_by_address(ip, address):
    """
    Convert address to coordinates using Nominatim API.
    Falls back to IP-based location on failure.
    
    Args:
        ip: User's IP address for fallback
        address: Physical address to geocode
        
    Returns:
        tuple: (latitude, longitude, timestamp)
    """
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json"
    headers = {'User-Agent': NOMINATIM_USER_AGENT}
    
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
    
    Args:
        ip: IP address to lookup
        
    Returns:
        tuple: (latitude, longitude, timestamp) or (None, None, None) on failure
    """
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


def get_user_last_location(user_id):
    """
    Retrieve user's most recent location data.
    
    Args:
        user_id: User identifier
        
    Returns:
        dict: Location data or None if not found
    """
    location = LocationRequest.query.filter_by(user_id=user_id)\
        .order_by(LocationRequest.timestamp.desc()).first()
    
    if location:
        return {
            "user_id": user_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": location.timestamp
        }
    return None


def get_nearest_volunteers(lat, lon, limit=DEFAULT_SEARCH_LIMIT, 
                         min_radius=MIN_SEARCH_RADIUS_KM,
                         max_radius=MAX_SEARCH_RADIUS_KM,
                         exception_id=set()):
    """
    Find nearest available volunteers using tile-based search system.
    
    Args:
        lat: Target latitude
        lon: Target longitude
        limit: Maximum number of volunteers to return
        min_radius: Minimum search radius in km
        max_radius: Maximum search radius in km
        exception_id: Set of volunteer IDs to exclude
        
    Returns:
        list: Sorted list of nearest available volunteers
    """
    center_tile_id = lat_lon_to_tile_id(lat, lon)
    volunteers = []
    volunteers_id = set()
    searched_tiles = set()
    tiles_to_search = [center_tile_id]

    # Initially we want all the neighbouring tiles as there might some closer points in them
    tiles_to_search.extend(get_neighboring_tiles(center_tile_id))
    
    while len(volunteers) < limit and len(tiles_to_search) > 0:
        tmp_tiles_to_search = []
        
        for current_tile in tiles_to_search:
            if current_tile in searched_tiles:
                continue
            searched_tiles.add(current_tile)
            
            # Query volunteers in current tile
            tile_volunteers = User.query.filter_by(
                is_volunteer=True,
                tile_id=current_tile
            ).all()

            for volunteer in tile_volunteers:
                volunteer_db = db.session.get(Volunteer, volunteer.id)
                
                # Skip if volunteer is unavailable or excluded
                if (volunteer.id in volunteers_id or
                    not volunteer_db or
                    not volunteer_db.availability or
                    volunteer.id in exception_id):
                    continue
                
                last_location = volunteer.location_requests[-1] if volunteer.location_requests else None
                
                if last_location:
                    distance = calculate_distance(lat, lon, 
                                               last_location.latitude,
                                               last_location.longitude)
                    
                    if min_radius <= distance <= max_radius:
                        volunteers.append({
                            "id": volunteer.id,
                            "distance": distance,
                            "location": {
                                "latitude": last_location.latitude,
                                "longitude": last_location.longitude
                            },
                            "last_login": volunteer.last_login
                        })
                        volunteers_id.add(volunteer.id)
            
            tmp_tiles_to_search.extend(get_neighboring_tiles(current_tile))
            
        if len(volunteers) >= limit or len(tmp_tiles_to_search) == 0:
            break
            
        tiles_to_search = tmp_tiles_to_search

    return sorted(volunteers, key=lambda v: v["distance"])[:limit]


def update_volunteer_availability(user_id, availability):
    """
    Update a volunteer's availability status.
    
    Args:
        user_id: Volunteer's user ID
        availability: New availability status
        
    Returns:
        dict: Updated volunteer info or error message
    """
    volunteer = db.session.get(Volunteer, user_id)
    if volunteer:
        volunteer.availability = availability
        db.session.commit()
        return {"id": user_id, "availability": availability}
    else:
        return {"error": "Volunteer not found"}