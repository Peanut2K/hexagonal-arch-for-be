# [CORE] use case ของ project — ใช้ 2 repo (projects + sites) และเรียก sites.service ข้าม feature
# ห้าม import: fastapi, pymongo, bson
from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import NotFound
from app.projects import schemas
from app.sites import service as sites_service

if TYPE_CHECKING:
    from app.projects.repo import ProjectRepo
    from app.sites.repo import SiteRepo


def create_project(projects: ProjectRepo, sites: SiteRepo, req: schemas.ProjectCreateRequest) -> dict:
    project_id = projects.create(req.name, req.description)
    sites_service.analyze_and_save(sites, req.geometry, f"Site 1 ({req.name})", project_id)
    return get_project(projects, sites, project_id)


def add_site_to_project(projects: ProjectRepo, sites: SiteRepo, project_id: str,
                        req: schemas.AddSiteToProjectRequest) -> dict:
    project = _must_get(projects, project_id)
    name = req.name or f"Site {sites.count_by_project(project_id) + 1} ({project['name']})"
    sites_service.analyze_and_save(sites, req.geometry, name, project_id)
    projects.touch(project_id)
    return get_project(projects, sites, project_id)


def list_projects(projects: ProjectRepo, sites: SiteRepo) -> list[dict]:
    # ponytail: N+1 count เหมือนโค้ดเดิม — project เยอะเมื่อไหร่ทำ count แบบ aggregate ใน SiteRepo
    return [{**p, "site_count": sites.count_by_project(p["id"])} for p in projects.list()]


def get_project(projects: ProjectRepo, sites: SiteRepo, project_id: str) -> dict:
    return {**_must_get(projects, project_id), "sites": sites.by_project(project_id)}


def delete_project(projects: ProjectRepo, sites: SiteRepo, project_id: str) -> dict:
    if not projects.delete(project_id):
        raise NotFound(f"Project '{project_id}' not found")
    sites.delete_by_project(project_id)
    return {"message": f"Project '{project_id}' deleted successfully"}


def _must_get(projects: ProjectRepo, project_id: str) -> dict:
    project = projects.get(project_id)
    if not project:
        raise NotFound(f"Project '{project_id}' not found")
    return project
