# ค่าจาก env + path — อ่านครั้งเดียวตอน import (main.py เรียก load_dotenv() ก่อน import ไฟล์นี้)
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BDI_DATA_DIR = ROOT / "bdi-data"

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def require_google_maps_api_key() -> str:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not configured.")
    return GOOGLE_MAPS_API_KEY
