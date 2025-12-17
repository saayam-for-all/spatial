import s2sphere
import math
from config import EARTH_RADIUS_KM, S2_LEVEL


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points using the Haversine formula.
    
    Args:
        lat1 (float): Latitude of first point in degrees
        lon1 (float): Longitude of first point in degrees
        lat2 (float): Latitude of second point in degrees
        lon2 (float): Longitude of second point in degrees
        
    Returns:
        float: Distance between points in kilometers
        
    Note:
        Uses the Haversine formula to calculate the great-circle distance
        between two points on a sphere (Earth).
    """
    # Convert all coordinates to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula components
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c
