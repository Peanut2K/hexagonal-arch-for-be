# [HTTP] /api/bdi/* — อ่าน CSV เป็น GeoJSON ตรง ๆ
# ponytail: ไม่มี service/repo เพราะไม่มี logic — แค่ส่งไฟล์ ถ้าเริ่มมีกฎค่อยแยก
from fastapi import APIRouter

from app.config import BDI_DATA_DIR
from app.shared.geo.load_csv_as_geojson import load_csv_as_geojson

router = APIRouter(tags=["BDI Data"], prefix="/bdi")


@router.get("/area", summary="Get Area Data")
def get_area_data():
    # zoning polygon ใหญ่ได้หลายกิโล (ตรวจด้วยมือแล้ว) → ข้าม repair/outlier check
    return load_csv_as_geojson(str(BDI_DATA_DIR / "area.csv"), skip_repair=True)


@router.get("/land", summary="Get Land Data")
def get_land_data():
    return load_csv_as_geojson(str(BDI_DATA_DIR / "land.csv"))


@router.get("/street", summary="Get Street Data")
def get_street_data():
    return load_csv_as_geojson(str(BDI_DATA_DIR / "street.csv"))


@router.get("/building-footprint", summary="Get Building Footprint Data")
def get_building_footprint_data():
    return load_csv_as_geojson(str(BDI_DATA_DIR / "building-footprint.csv"))
