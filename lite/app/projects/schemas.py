# [HTTP] Pydantic request/response — สัญญากับ frontend
# service import ไฟล์นี้ได้ (ยอมผูกกับ Pydantic แทนการทำ domain dataclass แยก)
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str
    geometry: dict
    description: str | None = None


class AddSiteToProjectRequest(BaseModel):
    geometry: dict
    name: str | None = None


class SiteResponse(BaseModel):
    id: str
    name: str
    geometry: dict
    analysis: dict  # ของจริงใช้ SiteAnalysis จาก sites/schemas.py
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    site_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    sites: list[SiteResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
