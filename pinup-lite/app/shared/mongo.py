# [ADAPTER] helper ที่ repo ทุกตัวใช้ร่วมกัน — service ห้าม import ไฟล์นี้
from bson import ObjectId
from bson.errors import InvalidId

from app.errors import AppError


def oid(value: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise AppError(f"Invalid {label}: {value}")


def out(doc: dict | None) -> dict | None:
    """Mongo doc → dict ธรรมดา: _id (ObjectId) กลายเป็น id (str)"""
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc
