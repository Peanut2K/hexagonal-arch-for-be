# [ADAPTER] สร้าง Mongo connection ครั้งเดียว — มีแค่ repo.py ของแต่ละ feature ที่ใช้
import os
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database


@lru_cache
def get_db() -> Database:
    return MongoClient(os.environ["MONGO_URI"])[os.environ["DB_NAME"]]
