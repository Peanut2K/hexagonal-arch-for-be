# [ADAPTER] ไฟล์เดียวของ feature นี้ที่รู้จัก Mongo (pymongo, bson, ชื่อ collection, ObjectId)
# คืนค่าเป็น dict ธรรมดาที่มี "id" เป็น str แล้ว → service ไม่เคยเห็น _id / ObjectId
# อยากเปลี่ยนเป็น Postgres → เขียนไฟล์นี้ใหม่ไฟล์เดียว
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database


def _oid(id: str) -> ObjectId | None:
    try:
        return ObjectId(id)
    except (InvalidId, TypeError):
        return None


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectRepo:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, description: str | None) -> str:
        now = _now()
        res = self.db.projects.insert_one(
            {"name": name, "description": description or "", "created_at": now, "updated_at": now}
        )
        return str(res.inserted_id)

    def get(self, project_id: str) -> dict | None:
        oid = _oid(project_id)
        doc = self.db.projects.find_one({"_id": oid}) if oid else None
        return _out(doc) if doc else None

    def list_with_site_count(self) -> list[dict]:
        # ponytail: N+1 count เหมือนโค้ดเดิม — project เยอะเมื่อไหร่เปลี่ยนเป็น $lookup ในไฟล์นี้ไฟล์เดียว
        return [
            {**_out(d), "site_count": self.count_sites(str(d["_id"]))}
            for d in self.db.projects.find().sort("created_at", -1)
        ]

    def count_sites(self, project_id: str) -> int:
        return self.db.sites.count_documents({"project_id": project_id})

    def sites_of(self, project_id: str) -> list[dict]:
        return [_out(d) for d in self.db.sites.find({"project_id": project_id}).sort("created_at", 1)]

    def add_site(self, project_id: str, name: str, geometry: dict, analysis: dict) -> None:
        now = _now()
        self.db.sites.insert_one(
            {"project_id": project_id, "name": name, "geometry": geometry,
             "analysis": analysis, "created_at": now, "updated_at": now}
        )
        self.db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"updated_at": now}})

    def delete(self, project_id: str) -> bool:
        oid = _oid(project_id)
        if not oid or self.db.projects.delete_one({"_id": oid}).deleted_count == 0:
            return False
        self.db.sites.delete_many({"project_id": project_id})
        return True
