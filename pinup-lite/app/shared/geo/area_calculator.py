import pyproj
from shapely.geometry import shape
from shapely.ops import transform

to_meters_transformer = pyproj.Transformer.from_crs(
    "EPSG:4326",   # WGS84
    "EPSG:32647",  # UTM Zone 47N (Thailand)
    always_xy=True
).transform

def calculate_area_m2(geometry_dict: dict) -> float:
    """
    ฟังก์ชันกลางสำหรับคำนวณพื้นที่ (ตารางเมตร)
    รองรับทั้งข้อมูลจากระบบเก่า และข้อมูล GeoJSON จากระบบใหม่
    """
    if not geometry_dict: 
        return 0.0
        
    try:
        geom_type = geometry_dict.get("type")
        if geom_type and geom_type not in ["Polygon", "MultiPolygon"]:
            return 0.0

        s_geom = shape(geometry_dict)
        
        projected = transform(to_meters_transformer, s_geom)
        
        return round(projected.area, 2) 
        
    except Exception as e:
        print(f"Error calculating area_m2: {e}")
        return 0.0

def calculate_area_km2(geometry_dict: dict) -> float:
    """
    ฟังก์ชันกลางสำหรับคำนวณพื้นที่ (ตารางกิโลเมตร)
    """
    if not geometry_dict:
        return 0.0
        
    area_m2 = calculate_area_m2(geometry_dict)
    return round(area_m2 / 1_000_000, 4)