# [ADAPTER] collection "sites" — ที่เดียวที่รู้จัก pymongo ของ feature นี้
# projects/service.py ก็ใช้ repo นี้ (นับ/ดึง/ลบ site ตาม project_id)
from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.database import Database

from app.shared.mongo import oid, out


def _site(doc: dict | None) -> dict | None:
    # default สำหรับ doc เก่าที่ field ไม่ครบ — เป็นเรื่องของข้อมูลใน DB จึงอยู่ใน repo
    if doc is None:
        return None
    now = datetime.utcnow()
    doc.setdefault("name", "Site")
    doc.setdefault("created_at", now)
    doc.setdefault("updated_at", now)
    return out(doc)


class SiteRepo:
    def __init__(self, db: Database):
        self.col = db.sites

    def insert(self, name: str, geometry: dict, analysis: dict, project_id: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        doc = {"name": name, "geometry": geometry, "analysis": analysis, "created_at": now, "updated_at": now}
        if project_id:
            doc["project_id"] = project_id
        self.col.insert_one(doc)
        return _site(doc)

    def get(self, site_id: str) -> dict | None:
        return _site(self.col.find_one({"_id": oid(site_id, "site_id")}))

    def update(self, site_id: str, fields: dict) -> dict | None:
        fields = {**fields, "updated_at": datetime.now(timezone.utc)}
        return _site(self.col.find_one_and_update(
            {"_id": oid(site_id, "site_id")}, {"$set": fields}, return_document=ReturnDocument.AFTER
        ))

    def delete(self, site_id: str) -> bool:
        return self.col.delete_one({"_id": oid(site_id, "site_id")}).deleted_count > 0

    def by_project(self, project_id: str) -> list[dict]:
        return [_site(d) for d in self.col.find({"project_id": project_id}).sort("created_at", 1)]

    def count_by_project(self, project_id: str) -> int:
        return self.col.count_documents({"project_id": project_id})

    def delete_by_project(self, project_id: str) -> None:
        self.col.delete_many({"project_id": project_id})
