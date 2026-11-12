# [HTTP] /api/{city_id}/bound-* — ขอบเขตการปกครอง
from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.admin import service
from app.admin.repo import BoundaryRepo
from app.db import get_db

router = APIRouter(tags=["Admin Boundaries"])


def get_repo(db: Database = Depends(get_db)) -> BoundaryRepo:
    return BoundaryRepo(db)


@router.get("/{city_id}/bound-mun")
def get_bound_mun(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_bound_mun(repo, city_id)


@router.get("/{city_id}/bound-tambon")
def get_bound_tambon(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_bound_tambon(repo, city_id)


@router.get("/{city_id}/bound-amphoe")
def get_bound_amphoe(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_bound_amphoe(repo, city_id)


@router.get("/{city_id}/bound-prov")
def get_bound_province(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_bound_province(repo, city_id)


@router.get("/{city_id}/bangkok-districts")
def get_bangkok_districts(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_bangkok_districts(repo, city_id)


@router.get("/{city_id}/metropolitan-districts")
def get_metropolitan_districts(city_id: str, repo: BoundaryRepo = Depends(get_repo)):
    return service.get_metropolitan_districts(repo, city_id)
