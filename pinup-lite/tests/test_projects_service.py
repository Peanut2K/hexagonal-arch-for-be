# test use case ของ projects โดยไม่มี Mongo / FastAPI / BDI CSV
# FakeRepo แค่มี method ชื่อเดียวกับ repo จริง — นี่คือประโยชน์ของการแยก service ออกจาก repo
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.errors import NotFound
from app.projects import schemas, service
from app.sites import service as sites_service

GEOM = {"type": "Polygon", "coordinates": [[[100.0, 13.0], [100.0, 13.1], [100.1, 13.1], [100.0, 13.0]]]}
T = datetime(2026, 1, 1)


@pytest.fixture(autouse=True)
def fake_analysis(monkeypatch):
    fake = SimpleNamespace(zoning_code="ย.1", model_dump=lambda: {"zoning_code": "ย.1"})
    monkeypatch.setattr(sites_service, "analyze_polygon_spatial", lambda geometry: fake)


class FakeProjects:
    def __init__(self):
        self.rows = {}

    def create(self, name, description):
        pid = f"p{len(self.rows) + 1}"
        self.rows[pid] = {"id": pid, "name": name, "description": description or "", "created_at": T, "updated_at": T}
        return pid

    def get(self, pid):
        return self.rows.get(pid)

    def list(self):
        return list(self.rows.values())

    def touch(self, pid):
        pass

    def delete(self, pid):
        return self.rows.pop(pid, None) is not None


class FakeSites:
    def __init__(self):
        self.rows = []

    def insert(self, name, geometry, analysis, project_id=None):
        row = {"id": f"s{len(self.rows) + 1}", "project_id": project_id, "name": name,
               "geometry": geometry, "analysis": analysis, "created_at": T, "updated_at": T}
        self.rows.append(row)
        return row

    def by_project(self, pid):
        return [r for r in self.rows if r["project_id"] == pid]

    def count_by_project(self, pid):
        return len(self.by_project(pid))

    def delete_by_project(self, pid):
        self.rows = [r for r in self.rows if r["project_id"] != pid]


def test_sites_are_numbered_per_project():
    projects, sites = FakeProjects(), FakeSites()
    p = service.create_project(projects, sites, schemas.ProjectCreateRequest(name="บางนา", geometry=GEOM))
    p = service.add_site_to_project(projects, sites, p["id"], schemas.AddSiteToProjectRequest(geometry=GEOM))
    assert [s["name"] for s in p["sites"]] == ["Site 1 (บางนา)", "Site 2 (บางนา)"]
    assert service.list_projects(projects, sites)[0]["site_count"] == 2


def test_delete_project_removes_its_sites():
    projects, sites = FakeProjects(), FakeSites()
    p = service.create_project(projects, sites, schemas.ProjectCreateRequest(name="x", geometry=GEOM))
    service.delete_project(projects, sites, p["id"])
    assert sites.rows == []
    with pytest.raises(NotFound):
        service.get_project(projects, sites, p["id"])
