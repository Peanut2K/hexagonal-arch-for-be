# [HTTP] /api/sites — ไม่มี logic. def (ไม่ใช่ async) เพราะ pymongo + shapely เป็น sync → รันใน threadpool
from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.sites import schemas, service
from app.sites.repo import SiteRepo

router = APIRouter(tags=["Site Spatial Analysis"], prefix="/sites")


def get_site_repo(db: Database = Depends(get_db)) -> SiteRepo:
    return SiteRepo(db)


@router.post("/analyze", response_model=schemas.SiteResponse, summary="Analyze Polygon & Create Site")
def analyze_site(body: schemas.SiteAnalyzeRequest, sites: SiteRepo = Depends(get_site_repo)):
    return service.create_site(sites, body)


@router.get("/{site_id}", response_model=schemas.SiteResponse, summary="Get Site Analysis by ID")
def get_site(site_id: str, sites: SiteRepo = Depends(get_site_repo)):
    return service.get_site(sites, site_id)


@router.put("/{site_id}", response_model=schemas.SiteResponse, summary="Re-analyze & Update Site")
def update_site(site_id: str, body: schemas.SiteAnalyzeRequest, sites: SiteRepo = Depends(get_site_repo)):
    return service.update_site(sites, site_id, body)


@router.delete("/{site_id}", summary="Delete Site Analysis")
def delete_site(site_id: str, sites: SiteRepo = Depends(get_site_repo)):
    return service.delete_site(sites, site_id)
