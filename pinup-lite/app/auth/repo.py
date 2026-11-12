# [ADAPTER] collection "users" — ค้น/แก้ด้วย email (unique) จึงไม่ต้องส่ง _id ออกไป
from pymongo import ReturnDocument
from pymongo.database import Database

from app.shared.mongo import out


class UserRepo:
    def __init__(self, db: Database):
        self.col = db.users

    def find_by_email(self, email: str) -> dict | None:
        return out(self.col.find_one({"email": email}))

    def insert(self, user: dict) -> dict:
        self.col.insert_one(user)  # insert_one เติม _id ลงใน dict ให้
        return out(user)

    def update(self, email: str, fields: dict) -> dict | None:
        return out(self.col.find_one_and_update(
            {"email": email}, {"$set": fields}, return_document=ReturnDocument.AFTER
        ))
