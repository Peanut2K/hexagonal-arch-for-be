# [ADAPTER] collection "projects" — site ของ project ไปถามที่ SiteRepo
from datetime import datetime, timezone

from pymongo.database import Database

from app.shared.mongo import oid, out


def _project(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    now = datetime.utcnow()
    doc.setdefault("name", "Project")
    doc.setdefault("description", "")
    doc.setdefault("created_at", now)
    doc.setdefault("updated_at", now)
    return out(doc)


class ProjectRepo:
    def __init__(self, db: Database):
        self.col = db.projects

    def create(self, name: str, description: str | None) -> str:
        now = datetime.now(timezone.utc)
        res = self.col.insert_one(
            {"name": name, "description": description or "", "created_at": now, "updated_at": now}
        )
        return str(res.inserted_id)

    def get(self, project_id: str) -> dict | None:
        return _project(self.col.find_one({"_id": oid(project_id, "project_id")}))

    def list(self) -> list[dict]:
        return [_project(d) for d in self.col.find().sort("created_at", -1)]

    def touch(self, project_id: str) -> None:
        self.col.update_one({"_id": oid(project_id, "project_id")},
                            {"$set": {"updated_at": datetime.now(timezone.utc)}})

    def delete(self, project_id: str) -> bool:
        return self.col.delete_one({"_id": oid(project_id, "project_id")}).deleted_count > 0
