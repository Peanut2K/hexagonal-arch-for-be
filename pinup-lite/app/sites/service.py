# [CORE] use case ของ site: วิเคราะห์ (analysis.py) แล้วบันทึก (repo)
# ห้าม import: fastapi, pymongo, bson
from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import NotFound
from app.sites import schemas
from app.sites.analysis import analyze_polygon_spatial

if TYPE_CHECKING:
    from app.sites.repo import SiteRepo


def analyze_and_save(sites: SiteRepo, geometry: dict, name: str | None = None,
                     project_id: str | None = None) -> dict:
    """projects/service.py เรียกตัวนี้ด้วย — ข้าม feature ผ่าน service เท่านั้น"""
    analysis = analyze_polygon_spatial(geometry)
    name = name or f"Site Analysis ({analysis.zoning_code})"
    return sites.insert(name, geometry, analysis.model_dump(), project_id)


def create_site(sites: SiteRepo, req: schemas.SiteAnalyzeRequest) -> dict:
    return analyze_and_save(sites, req.geometry, req.name)


def get_site(sites: SiteRepo, site_id: str) -> dict:
    site = sites.get(site_id)
    if not site:
        raise NotFound(f"Site '{site_id}' not found")
    return site


def update_site(sites: SiteRepo, site_id: str, req: schemas.SiteAnalyzeRequest) -> dict:
    existing = get_site(sites, site_id)
    analysis = analyze_polygon_spatial(req.geometry)
    name = req.name or existing.get("name") or f"Site Analysis ({analysis.zoning_code})"
    return sites.update(site_id, {"name": name, "geometry": req.geometry, "analysis": analysis.model_dump()})


def delete_site(sites: SiteRepo, site_id: str) -> dict:
    if not sites.delete(site_id):
        raise NotFound(f"Site '{site_id}' not found")
    return {"message": f"Site '{site_id}' deleted successfully"}
