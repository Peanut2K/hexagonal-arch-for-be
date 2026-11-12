def swap_lon_lat(coords):
    """
    Recursively traverses a coordinate array and swaps [lon, lat] to [lat, lon].
    This is highly reusable for converting standard GeoJSON (lon, lat) to 
    Google Maps format (lat, lon).
    """
    if not isinstance(coords, list):
        return coords
        
    if len(coords) == 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
        return [coords[1], coords[0]] # [lat, lon]
        
    return [swap_lon_lat(c) for c in coords]
