# [HTTP] รับ request → เรียก service → คืน response. ไม่มี logic, ไม่แตะ db ตรง
# get_repo = จุดเดียวที่ผูก "service ใช้ repo ตัวไหน" (composition root ฉบับย่อ)
# test ทั้งเส้นโดยไม่ต่อ DB: app.dependency_overrides[get_repo] = lambda: FakeRepo()
from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db import get_db
from app.projects import schemas, service
from app.projects.repo import ProjectRepo

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_repo(db: Database = Depends(get_db)) -> ProjectRepo:
    return ProjectRepo(db)


# ใช้ def (ไม่ใช่ async def) เพราะ pymongo เป็น sync → FastAPI รันใน threadpool ไม่ block event loop
@router.post("", response_model=schemas.ProjectResponse)
def create_project(body: schemas.ProjectCreateRequest, repo: ProjectRepo = Depends(get_repo)):
    return service.create_project(repo, body)


@router.post("/{project_id}/sites", response_model=schemas.ProjectResponse)
def add_site_to_project(project_id: str, body: schemas.AddSiteToProjectRequest, repo: ProjectRepo = Depends(get_repo)):
    return service.add_site_to_project(repo, project_id, body)


@router.get("", response_model=list[schemas.ProjectListItem])
def list_projects(repo: ProjectRepo = Depends(get_repo)):
    return service.list_projects(repo)


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: str, repo: ProjectRepo = Depends(get_repo)):
    return service.get_project(repo, project_id)


@router.delete("/{project_id}")
def delete_project(project_id: str, repo: ProjectRepo = Depends(get_repo)):
    return service.delete_project(repo, project_id)
