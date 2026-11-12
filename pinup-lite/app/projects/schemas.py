from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.sites.schemas import SiteResponse


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name", example="พระนคร-approved")
    geometry: dict = Field(..., description="Initial GeoJSON Polygon geometry")
    description: Optional[str] = Field(None, description="Optional project description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "บางนา-approved",
                "description": "โครงการพัฒนาอสังหาริมทรัพย์โซนบางนา",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [100.6231, 13.6783],
                            [100.6231, 13.6788],
                            [100.6236, 13.6788],
                            [100.6236, 13.6783],
                            [100.6231, 13.6783],
                        ]
                    ],
                },
            }
        }
    }


class AddSiteToProjectRequest(BaseModel):
    geometry: dict = Field(..., description="GeoJSON Polygon geometry to add")
    name: Optional[str] = Field(None, description="Optional site name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "แปลงย่อยที่ 2 (บางนา)",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [100.6240, 13.6785],
                            [100.6240, 13.6790],
                            [100.6245, 13.6790],
                            [100.6245, 13.6785],
                            [100.6240, 13.6785],
                        ]
                    ],
                },
            }
        }
    }


class ProjectListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    site_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sites: List[SiteResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
