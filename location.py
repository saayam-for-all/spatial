from models import User, LocationRequest, Volunteer
from extensions import db
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
import requests
from sqlalchemy import text
from config import (
    DEFAULT_SEARCH_LIMIT,
    MIN_SEARCH_RADIUS_KM,
    MAX_SEARCH_RADIUS_KM,
    NOMINATIM_USER_AGENT
)
from util import lat_lon_to_tile_id, get_neighboring_tiles, calculate_distance
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT, timeout=5)
_reverse = RateLimiter(_geolocator.reverse, min_delay_seconds=1.0)

DEFAULT_SEARCH_LIMIT = 5 
MAX_LOCATIONS_PER_USER = 1  # Keep only the most recent entry per user
MAX_LOCATION_AGE_DAYS = 30  # Delete entries older than 30 days

def _get_city_name(lat: float, lon: float) -> str | None:
    try:
        loc = _reverse((lat, lon), language="en", zoom=10)
        if not loc:
            return None
        addr = (loc.raw or {}).get("address", {})
        for key in ("city", "town", "village", "municipality", "hamlet", "county"):
            if addr.get(key):
                return addr[key]
        return addr.get("state") or addr.get("region")
    except Exception as e:
        print(f"Reverse geocoding failed for ({lat}, {lon}): {e}")
        return None

def process_location_data(user_id, lat, lon, timestamp, is_volunteer, availability):
    user = db.session.get(User, user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        if is_volunteer:
            volunteer = Volunteer(id=user_id, availability=availability)
            db.session.add(volunteer)
    else:
        if is_volunteer:
            volunteer = db.session.get(Volunteer, user_id)
            if not volunteer:
                volunteer = Volunteer(id=user_id, availability=availability)
                db.session.add(volunteer)
            else:
                volunteer.availability = availability

    tile_id = lat_lon_to_tile_id(lat, lon)
    user.tile_id = tile_id
    user.last_login = timestamp
    user.is_volunteer = is_volunteer

    # Eviction logic: delete old or extra entries
    old_entries = LocationRequest.query.filter(
        LocationRequest.user_id == user_id
    ).order_by(LocationRequest.timestamp.desc()).offset(MAX_LOCATIONS_PER_USER).all()

    for entry in old_entries:
        db.session.delete(entry)

    expiration_time = datetime.now(timezone.utc) - timedelta(days=MAX_LOCATION_AGE_DAYS)
    stale_entries = LocationRequest.query.filter(
        LocationRequest.timestamp < expiration_time
    ).all()
    for entry in stale_entries:
        db.session.delete(entry)

    city = _get_city_name(lat, lon)

    location_request = LocationRequest(
        user_id=user_id,
        latitude=lat,
        longitude=lon,
        timestamp=timestamp,
        city_name=city
    )
    db.session.add(location_request)
    db.session.commit()

    return {
        "latitude": lat,
        "longitude": lon,
        "timestamp": user.last_login,
        "city_name": city
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
            "timestamp": location.timestamp,
            "city_name": location.city_name
        }
    return None


# def get_nearest_volunteers(lat, lon, limit=DEFAULT_SEARCH_LIMIT, 
#                          min_radius=MIN_SEARCH_RADIUS_KM,
#                          max_radius=MAX_SEARCH_RADIUS_KM,
#                          exception_id=None):
#     exception_id = exception_id or set()
#     """
#     Find nearest available volunteers using tile-based search system.
    
#     Args:
#         lat: Target latitude
#         lon: Target longitude
#         limit: Maximum number of volunteers to return
#         min_radius: Minimum search radius in km
#         max_radius: Maximum search radius in km
#         exception_id: Set of volunteer IDs to exclude
        
#     Returns:
#         list: Sorted list of nearest available volunteers
#     """
#     center_tile_id = lat_lon_to_tile_id(lat, lon)
#     volunteers = []
#     volunteers_id = set()
#     searched_tiles = set()
#     tiles_to_search = [center_tile_id]

#     # Initially we want all the neighbouring tiles as there might some closer points in them
#     tiles_to_search.extend(get_neighboring_tiles(center_tile_id))
    
#     while len(volunteers) < limit and len(tiles_to_search) > 0:
#         tmp_tiles_to_search = []
        
#         for current_tile in tiles_to_search:
#             if current_tile in searched_tiles:
#                 continue
#             searched_tiles.add(current_tile)
            
#             # Query volunteers in current tile
#             tile_volunteers = User.query.filter_by(
#                 is_volunteer=True,
#                 tile_id=current_tile
#             ).all()

#             for volunteer in tile_volunteers:
#                 volunteer_db = db.session.get(Volunteer, volunteer.id)
                
#                 # Skip if volunteer is unavailable or excluded
#                 if (volunteer.id in volunteers_id or
#                     not volunteer_db or
#                     not volunteer_db.availability or
#                     volunteer.id in exception_id):
#                     continue
                
#                 last_location = volunteer.location_requests[-1] if volunteer.location_requests else None
                
#                 if last_location:
#                     distance = calculate_distance(lat, lon, 
#                                                last_location.latitude,
#                                                last_location.longitude)
                    
#                     if min_radius <= distance <= max_radius:
#                         volunteers.append({
#                             "id": volunteer.id,
#                             "distance": distance,
#                             "location": {
#                                 "latitude": last_location.latitude,
#                                 "longitude": last_location.longitude,
#                                 "city_name": getattr(last_location, "city_name", None),
#                             },
#                             "last_login": volunteer.last_login
#                         })
#                         volunteers_id.add(volunteer.id)
            
#             tmp_tiles_to_search.extend(get_neighboring_tiles(current_tile))
            
#         if len(volunteers) >= limit or len(tmp_tiles_to_search) == 0:
#             break
            
#         tiles_to_search = tmp_tiles_to_search

#     return sorted(volunteers, key=lambda v: v["distance"])[:limit]


def get_nearest_volunteers_with_postgis(lat: float, lon: float, limit=DEFAULT_SEARCH_LIMIT, min_radius_km=0, max_radius_km=1000, exception_id=None):
    """
    Finds nearest available volunteers using a single, efficient PostGIS query.
    This function replaces the slow, manual tile-based search.
    """
    exception_id = exception_id or set()

    # Create a geographic point from the user's coordinates for the query
    user_point = f'SRID=4326;POINT({lon} {lat})'

    # This single query does everything the old function did, but inside the database.
    # It finds volunteers, checks availability, calculates distance, and filters by radius.
    query = text("""
        SELECT
            u.id,
            lr.latitude,
            lr.longitude,
            lr.city_name,
            -- Use ST_Distance to calculate the precise distance on a sphere (in meters)
            ST_Distance(
                ST_MakePoint(lr.longitude, lr.latitude)::geography,
                :user_point::geography
            ) AS distance_in_meters
        FROM
            users AS u
        JOIN
            volunteers AS v ON u.id = v.id
        -- Find the MOST RECENT location for each volunteer
        JOIN
            location_request AS lr ON lr.id = (
                SELECT id FROM location_request
                WHERE user_id = u.id
                ORDER BY timestamp DESC
                LIMIT 1
            )
        WHERE
            u.is_volunteer = TRUE
            AND v.availability = TRUE
            AND u.id NOT IN :exception_ids
            -- This is the main distance filter
            AND ST_Distance(
                ST_MakePoint(lr.longitude, lr.latitude)::geography,
                :user_point::geography
            ) BETWEEN :min_dist_meters AND :max_dist_meters
        ORDER BY
            distance_in_meters ASC
        LIMIT :limit;
    """)

    # Convert radius from km to meters for the query
    min_dist_meters = min_radius_km * 1000
    max_dist_meters = max_radius_km * 1000
    
    # Execute the query with all parameters
    results = db.session.execute(query, {
        "user_point": user_point,
        "exception_ids": tuple(exception_id) if exception_id else (None,),
        "min_dist_meters": min_dist_meters,
        "max_dist_meters": max_dist_meters,
        "limit": limit
    }).fetchall()

    # Format the results into a clean list
    volunteers = []
    for row in results:
        volunteers.append({
            "id": row.id,
            "distance_km": round(row.distance_in_meters / 1000, 2),
            "location": {
                "latitude": row.latitude,
                "longitude": row.longitude,
                "city_name": row.city_name,
            }
        })

    return volunteers


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