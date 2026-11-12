# [HTTP] /api/projects — ไม่มี logic
from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.projects import schemas, service
from app.projects.repo import ProjectRepo
from app.sites.repo import SiteRepo
from app.sites.router import get_site_repo

router = APIRouter(tags=["Projects & Site Persistence"], prefix="/projects")


def get_project_repo(db: Database = Depends(get_db)) -> ProjectRepo:
    return ProjectRepo(db)


Projects = Depends(get_project_repo)
Sites = Depends(get_site_repo)


@router.post("", response_model=schemas.ProjectResponse, summary="Create New Project with Site Polygon")
def create_project(body: schemas.ProjectCreateRequest, projects: ProjectRepo = Projects, sites: SiteRepo = Sites):
    return service.create_project(projects, sites, body)


@router.post("/{project_id}/sites", response_model=schemas.ProjectResponse, summary="Add Polygon to Existing Project")
def add_site_to_project(project_id: str, body: schemas.AddSiteToProjectRequest,
                        projects: ProjectRepo = Projects, sites: SiteRepo = Sites):
    return service.add_site_to_project(projects, sites, project_id, body)


@router.get("", response_model=list[schemas.ProjectListItem], summary="List All Projects for UI Dropdown")
def list_projects(projects: ProjectRepo = Projects, sites: SiteRepo = Sites):
    return service.list_projects(projects, sites)


@router.get("/{project_id}", response_model=schemas.ProjectResponse, summary="Get Project Details by ID")
def get_project(project_id: str, projects: ProjectRepo = Projects, sites: SiteRepo = Sites):
    return service.get_project(projects, sites, project_id)


@router.delete("/{project_id}", summary="Delete Project")
def delete_project(project_id: str, projects: ProjectRepo = Projects, sites: SiteRepo = Sites):
    return service.delete_project(projects, sites, project_id)
