# [CORE] business logic ของ projects
# ห้าม import: fastapi, pymongo, bson   ← กฎข้อเดียวที่ต้องรักษา
# รับ repo เข้ามาเป็น parameter (แทน db เดิม) → test ด้วย FakeRepo ได้
from __future__ import annotations

from typing import TYPE_CHECKING

from app.errors import NotFound
from app.projects import schemas
from app.sites.analysis import analyze_polygon

if TYPE_CHECKING:  # ใช้แค่ type hint — runtime ไม่ import pymongo
    from app.projects.repo import ProjectRepo


def create_project(repo: ProjectRepo, req: schemas.ProjectCreateRequest) -> dict:
    project_id = repo.create(req.name, req.description)
    repo.add_site(project_id, f"Site 1 ({req.name})", req.geometry, analyze_polygon(req.geometry))
    return get_project(repo, project_id)


def add_site_to_project(repo: ProjectRepo, project_id: str, req: schemas.AddSiteToProjectRequest) -> dict:
    project = _must_get(repo, project_id)
    name = req.name or f"Site {repo.count_sites(project_id) + 1} ({project['name']})"
    repo.add_site(project_id, name, req.geometry, analyze_polygon(req.geometry))
    return get_project(repo, project_id)


def list_projects(repo: ProjectRepo) -> list[dict]:
    return repo.list_with_site_count()


def get_project(repo: ProjectRepo, project_id: str) -> dict:
    return {**_must_get(repo, project_id), "sites": repo.sites_of(project_id)}


def delete_project(repo: ProjectRepo, project_id: str) -> dict:
    if not repo.delete(project_id):
        raise NotFound(f"Project '{project_id}' not found")
    return {"message": f"Project '{project_id}' deleted successfully"}


def _must_get(repo: ProjectRepo, project_id: str) -> dict:
    project = repo.get(project_id)
    if not project:
        raise NotFound(f"Project '{project_id}' not found")
    return project
