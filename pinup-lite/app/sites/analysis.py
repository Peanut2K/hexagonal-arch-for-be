# [CORE] วิเคราะห์ polygon เทียบ BDI dataset — pure: geometry เข้า → SiteAnalysis ออก
# ไม่แตะ DB, ไม่แตะ HTTP (ย้ายมาจาก services/sites_service.py ทั้งก้อน ไม่ได้แก้ logic)
import os

from shapely.geometry import shape

from app.config import BDI_DATA_DIR
from app.shared.geo.area_calculator import calculate_area_m2
from app.shared.geo.load_csv_with_geo import load_csv_with_geo
from app.sites import schemas
from app.sites.risk import evaluate_geographic_risks
from app.sites.zoning_mapping import get_zoning_info
from app.sites.zoning_rules import get_main_zoning_regulations

VACANT_LAND_TYPES = {"แปลงที่ดินเปล่า", "ที่ว่างเปล่า", "-"}


def extract_address_components(address_str: str) -> tuple[str, str, str, str]:
    """Parses subdistrict, district, province, zipcode from address string."""
    subdistrict, district, province, zipcode = "-", "-", "-", "-"
    if not address_str:
        return subdistrict, district, province, zipcode

    parts = address_str.split()
    for p in parts:
        if "แขวง" in p:
            subdistrict = p.replace("แขวง", "").strip()
        elif "เขต" in p:
            district = p.replace("เขต", "").strip()
        elif "กรุงเทพ" in p or "จังหวัด" in p:
            province = p.replace("จังหวัด", "").strip()
        elif p.isdigit() and len(p) == 5:
            zipcode = p.strip()
    return subdistrict, district, province, zipcode


def fetch_zoning_regulations(code_key: str) -> list:
    """Fetch allowed main land use regulations per Bangkok Comprehensive Zoning Plan 2556."""
    raw_list = get_main_zoning_regulations(code_key)
    return [
        schemas.ZoningRegulationItem(
            category=item.get("category", "ทั่วไป"),
            activity=item["activity"],
            condition=item["condition"],
            note=item["note"],
        )
        for item in raw_list
    ]


def row_to_shapely_geometry(row: dict):
    """Converts a BDI CSV row with GEO_COOR coordinates list into a Shapely shape."""
    raw_coords = row.get("GEO_COOR")
    if not raw_coords:
        return None
    gtype = str(row.get("GEO_TYPE", "Polygon")).strip().capitalize()
    if gtype in ["Polygon", "Street"]:
        gtype = "Polygon"
    try:
        return shape({"type": gtype, "coordinates": raw_coords})
    except Exception:
        return None


def analyze_polygon_spatial(geometry: dict) -> schemas.SiteAnalysis:
    site_shape = shape(geometry)
    area_m2 = round(calculate_area_m2(geometry), 2)

    # 1. Analyze Area Dataset (area.csv) — get zoning code & color
    area_file = os.path.join(BDI_DATA_DIR, "area.csv")
    area_rows = load_csv_with_geo(area_file, swap_coords=False)

    zoning_code = "-"
    zoning_color = "#808080"

    for r in area_rows:
        area_shape = row_to_shapely_geometry(r)
        if area_shape and (site_shape.intersects(area_shape) or site_shape.within(area_shape)):
            zoning_code = r.get("ZONING_CODE", zoning_code)
            zoning_color = r.get("ZONING_COLOR", zoning_color)
            break

    z_info = get_zoning_info(zoning_code)
    far = z_info["far"]
    osr = z_info["osr"]
    gfa_max = round(area_m2 * far, 2)

    # 2. Analyze Land Dataset (land.csv) — get address & land status
    land_file = os.path.join(BDI_DATA_DIR, "land.csv")
    land_rows = load_csv_with_geo(land_file, swap_coords=False)

    address_full = "-"
    land_status = "-"

    for r in land_rows:
        l_shape = row_to_shapely_geometry(r)
        if l_shape and site_shape.intersects(l_shape):
            address_full = r.get("ADDRESS_NAME", address_full)
            land_status = r.get("BUILDING_TYPE", land_status)
            break

    # Map BUILDING_TYPE → ownership_status
    ownership_status = "ไม่มีเจ้าของ" if land_status in VACANT_LAND_TYPES else "มีเจ้าของ"

    subdistrict, district, province, zipcode = extract_address_components(address_full)

    # 3. Analyze Street Dataset (street.csv) — 500m Buffer & Road Priority
    street_file = os.path.join(BDI_DATA_DIR, "street.csv")
    street_rows = load_csv_with_geo(street_file, swap_coords=False)

    BUFFER_500M = 0.0045045  # approx 500m in WGS84 degrees
    candidates_500m = []
    closest_road = None
    min_dist = float("inf")

    for r in street_rows:
        st_shape = row_to_shapely_geometry(r)
        if not st_shape or not r.get("STREET_NAME"):
            continue

        dist = site_shape.distance(st_shape)
        if dist < min_dist:
            min_dist = dist
            closest_road = r

        if dist <= BUFFER_500M:
            candidates_500m.append((r, dist))

    # Priority: Major road ("ถนน") in 500m > Any road in 500m > Closest overall road
    selected_road = None
    if candidates_500m:
        major_roads = [item for item in candidates_500m if "ถนน" in item[0].get("STREET_NAME", "")]
        selected_list = major_roads if major_roads else candidates_500m
        selected_list.sort(key=lambda x: x[1])
        selected_road = selected_list[0][0]
    elif closest_road:
        selected_road = closest_road

    nearest_road_name = "-"
    nearest_road_type = "-"
    nearest_road_width_m = 0.0

    if selected_road:
        nearest_road_name = selected_road.get("STREET_NAME", "-")
        if "ถนน" in nearest_road_name:
            nearest_road_type = "ถนนสาธารณะ"
            nearest_road_width_m = 16.0
        else:
            nearest_road_type = "ซอยสาธารณประโยชน์"
            nearest_road_width_m = 12.0

    # 4. Fetch Main Zoning Regulations
    code_key = z_info["zoning_code_key"]
    regulations = fetch_zoning_regulations(code_key)

    # 5. Evaluate Geographic & Flood Risks Dynamically
    risk_info = evaluate_geographic_risks(district, subdistrict, province)

    return schemas.SiteAnalysis(
        zoning_code=zoning_code,
        zoning_name=z_info["name"],
        zoning_color=zoning_color,
        address=address_full,
        subdistrict=subdistrict,
        district=district,
        province=province,
        zipcode=zipcode,
        land_status=land_status,
        ownership_status=ownership_status,
        area_sqm=area_m2,
        cadastral=[],
        regulations=regulations,
        nearest_road_name=nearest_road_name,
        nearest_road_type=nearest_road_type,
        nearest_road_width_m=nearest_road_width_m,
        flood_risk=risk_info["flood_risk"],
        landslide_risk=risk_info["landslide_risk"],
        soil_settlement_risk=risk_info["soil_settlement_risk"],
        risk_alert_text=risk_info["risk_alert_text"],
        far=far,
        far_bonus=0.0,
        osr=osr,
        gfa_max=gfa_max,
    )
