import s2sphere
import math

EARTH_RADIUS_KM = 6371
S2_LEVEL = 5

def lat_lon_to_tile_id(lat, lon):
    lat_lng = s2sphere.LatLng.from_degrees(lat, lon)
    cell = s2sphere.CellId.from_lat_lng(lat_lng).parent(S2_LEVEL)
    return cell.to_token()

def get_neighboring_tiles(tile_id):
    cell = s2sphere.CellId.from_token(tile_id)
    neighbors = [n.to_token() for n in cell.get_all_neighbors(S2_LEVEL)]
    return neighbors

def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c