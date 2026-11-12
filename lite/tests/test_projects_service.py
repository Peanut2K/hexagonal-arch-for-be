# test service โดยไม่มี Mongo / FastAPI — FakeRepo มี method ชื่อเดียวกับ ProjectRepo ก็พอ
from datetime import datetime

import pytest

from app.errors import NotFound
from app.projects import schemas, service

GEOM = {"type": "Polygon", "coordinates": [[[100.0, 13.0], [100.0, 13.1], [100.1, 13.1], [100.0, 13.0]]]}
T = datetime(2026, 1, 1)


class FakeRepo:
    def __init__(self):
        self.projects, self.sites = {}, []

    def create(self, name, description):
        pid = str(len(self.projects) + 1)
        self.projects[pid] = {"id": pid, "name": name, "description": description, "created_at": T, "updated_at": T}
        return pid

    def get(self, pid):
        return self.projects.get(pid)

    def count_sites(self, pid):
        return len(self.sites_of(pid))

    def sites_of(self, pid):
        return [s for s in self.sites if s["project_id"] == pid]

    def add_site(self, pid, name, geometry, analysis):
        self.sites.append({"id": str(len(self.sites) + 1), "project_id": pid, "name": name, "geometry": geometry,
                           "analysis": analysis, "created_at": T, "updated_at": T})

    def delete(self, pid):
        return self.projects.pop(pid, None) is not None


def test_create_then_add_site_names_sites_in_order():
    repo = FakeRepo()
    p = service.create_project(repo, schemas.ProjectCreateRequest(name="บางนา", geometry=GEOM))
    p = service.add_site_to_project(repo, p["id"], schemas.AddSiteToProjectRequest(geometry=GEOM))
    assert [s["name"] for s in p["sites"]] == ["Site 1 (บางนา)", "Site 2 (บางนา)"]


def test_missing_project_raises_not_found():
    with pytest.raises(NotFound):
        service.get_project(FakeRepo(), "nope")
    with pytest.raises(NotFound):
        service.delete_project(FakeRepo(), "nope")
