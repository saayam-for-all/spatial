import s2sphere
import math
from config import EARTH_RADIUS_KM, S2_LEVEL


def lat_lon_to_tile_id(lat, lon):
    """
    Convert latitude and longitude coordinates to an S2 tile ID.
    
    Args:
        lat (float): Latitude in degrees
        lon (float): Longitude in degrees
        
    Returns:
        str: S2 cell token representing the tile containing the coordinates
        
    Note:
        Uses S2 Geometry library to convert geographic coordinates into
        hierarchical space-filling curve indexes.
    """
    lat_lng = s2sphere.LatLng.from_degrees(lat, lon)
    cell = s2sphere.CellId.from_lat_lng(lat_lng).parent(S2_LEVEL)
    return cell.to_token()


def tile_id_to_bounds(tile_id):
    """
    Convert an S2 tile ID to its geographic bounding box.
    
    Args:
        tile_id (str): S2 cell token
        
    Returns:
        tuple: (min_lat, min_lon, max_lat, max_lon) in degrees representing
               the rectangular bounds of the tile
    """
    cell = s2sphere.Cell(s2sphere.CellId.from_token(tile_id))
    rect = cell.get_rect_bound()
    return (
        rect.lo().lat().degrees,
        rect.lo().lng().degrees,
        rect.hi().lat().degrees,
        rect.hi().lng().degrees
    )


def get_neighboring_tiles(tile_id):
    """
    Get the IDs of all adjacent tiles for a given tile.
    
    Args:
        tile_id (str): S2 cell token
        
    Returns:
        list: S2 cell tokens of all neighboring tiles at the same level
    """
    cell = s2sphere.CellId.from_token(tile_id)
    neighbors = [n.to_token() for n in cell.get_all_neighbors(S2_LEVEL)]
    return neighbors


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