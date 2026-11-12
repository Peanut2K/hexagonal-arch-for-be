# [CORE] จัดรูป properties ของขอบเขตแต่ละประเภท → GeoJSON FeatureCollection
# ห้าม import: fastapi, pymongo, bson
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from app.errors import NotFound

if TYPE_CHECKING:
    from app.admin.repo import BoundaryRepo


def _collection(features: list[dict] | None, fmt: Callable[[dict], dict], missing: str) -> dict:
    if features is None:
        raise NotFound(missing)
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": f["id"], "geometry": f["geometry"], "properties": fmt(f["properties"])}
            for f in features
        ],
    }


def get_bound_mun(repo: BoundaryRepo, city_id: str) -> dict:
    def fmt(p):
        return {
            "id": p.get("Id"),
            "name_th": p.get("NAME_T"),
            "name_en": p.get("NAME_E"),
            "display_name": f"{p.get('NAME_T', '')} ({p.get('NAME_E', '')})",
        }
    return _collection(repo.features_in_city("bound_mun", city_id.upper()), fmt, "Dataset 'bound_mun' not found")


def get_bound_tambon(repo: BoundaryRepo, city_id: str) -> dict:
    def fmt(p):
        t_en = (p.get("T_NAME_E") or "").title()
        a_en = (p.get("A_NAME_E") or "").title()
        p_en = (p.get("P_NAME_E") or "").title()
        return {
            "id": p.get("OBJECTID"),
            "tambon_th": p.get("T_NAME_T"),
            "tambon_en": t_en,
            "amphoe_th": p.get("A_NAME_T"),
            "amphoe_en": a_en,
            "province_th": p.get("P_NAME_T"),
            "province_en": p_en,
            "display_multiline": [
                {"label": "ตำบล", "th": p.get("T_NAME_T"), "en": t_en, "highlight": True},
                {"label": "อำเภอ", "th": p.get("A_NAME_T"), "en": a_en, "highlight": False},
                {"label": "จังหวัด", "th": p.get("P_NAME_T"), "en": p_en, "highlight": False},
            ],
        }
    return _collection(repo.features_in_city("bound_tambon", city_id.upper()), fmt, "Dataset 'bound_tambon' not found")


def get_bound_amphoe(repo: BoundaryRepo, city_id: str) -> dict:
    def fmt(p):
        return {
            "name_th": p.get("AMP_NAME_T"),
            "name_en": p.get("AMP_NAME_E"),
            "display_name": f"{p.get('AMP_NAME_T', '')} ({p.get('AMP_NAME_E', '')})",
        }
    return _collection(repo.features_in_city("bound_amphoe", city_id.upper()), fmt, "Dataset 'bound_amphoe' not found")


def get_bound_province(repo: BoundaryRepo, city_id: str) -> dict:
    def fmt(p):
        try:
            area = float(p["Area_km2_"]) if p.get("Area_km2_") is not None else 0.0
        except ValueError:
            area = 0.0
        return {
            "name_th": p.get("PROV_NAMT"),
            "name_en": p.get("PROV_NAME"),
            "area_km2": area,
            "display_name": f"{p.get('PROV_NAMT', '')} ({p.get('PROV_NAME', '')}) - {area:.2f} ตร.กม.",
        }
    return _collection(repo.features_in_city("bound_province", city_id.upper()), fmt, "Dataset 'bound_province' not found")


def _district_fmt(prefix: str, kind: str, fallback: str) -> Callable[[dict], dict]:
    def fmt(p):
        name = p.get("_LAYER_NAME", p.get("AD_LTYPE", fallback))
        return {
            "name": name,
            "display_name": f"{prefix}: {name}",
            "type": kind,
            "perimeter_meters": round(p.get("SHAPE.LEN", 0.0), 2),
        }
    return fmt


def get_bangkok_districts(repo: BoundaryRepo, city_id: str) -> dict:
    city = city_id.upper()
    return _collection(
        repo.features_of_city_dataset("47_เขตการปกครอง_กทม", city),
        _district_fmt("เขต", "เขต (District)", "ไม่ระบุชื่อเขต"),
        f"Dataset 'bangkok_districts' not found for {city}",
    )


def get_metropolitan_districts(repo: BoundaryRepo, city_id: str) -> dict:
    city = city_id.upper()
    return _collection(
        repo.features_of_city_dataset("48_เขตการปกครองปริมณฑล", city),
        _district_fmt("ปริมณฑล", "อำเภอ (Metropolitan District)", "ไม่ระบุชื่อปริมณฑล"),
        f"Dataset 'metropolitan_districts' not found for {city}",
    )
