# [ADAPTER] Mongo connection ครั้งเดียวทั้งแอป — ใช้ผ่าน repo.py ของแต่ละ feature เท่านั้น
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import DB_NAME, MONGO_URI


@lru_cache
def get_db() -> Database:
    if not MONGO_URI:
        raise ValueError("MONGO_URI not configured. Cannot connect to Database.")
    db = MongoClient(MONGO_URI)[DB_NAME]
    db.sites.create_index("project_id")
    return db
