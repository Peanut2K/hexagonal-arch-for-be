import csv
from app.shared.geo.parse_malformed_geo_json import parse_malformed_geo_json
from app.shared.geo.swap_lon_lat import swap_lon_lat

def load_csv_with_geo(file_path: str, geo_col: str = 'GEO_COOR', swap_coords: bool = True):
    """
    Generic helper function to read a CSV file, parse its geometry column, 
    and optionally swap the coordinates for Google Maps compatibility.
    """
    results = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if geo_col in row and row[geo_col]:
                    parsed_geo = parse_malformed_geo_json(row[geo_col])
                    if swap_coords:
                        parsed_geo = swap_lon_lat(parsed_geo)
                    row[geo_col] = parsed_geo
                results.append(row)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
    return results
