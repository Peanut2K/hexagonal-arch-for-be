# [CORE] กฎ/การคำนวณล้วน — ไม่แตะ DB, ไม่แตะ HTTP
# ใน pinup-backend: ย้าย analyze_polygon_spatial() + helper ของมัน
# (extract_address_components, row_to_shapely_geometry, ...) จาก services/sites_service.py
# มาวางที่นี่ทั้งก้อน มัน pure อยู่แล้ว ไม่ต้องแก้ข้างใน


def analyze_polygon(geometry: dict) -> dict:
    # ponytail: stub ให้ skeleton รันได้ — ของจริงคือ analyze_polygon_spatial(geometry).model_dump()
    return {"zoning_code": "-", "area_sqm": 0.0}
