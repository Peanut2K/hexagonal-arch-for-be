# [CORE] ค้นหาสถานที่ (ตอนนี้ใช้ mock data)
from app.search.mock_data import MOCK_LOCATIONS


def search_locations(query: str) -> list[dict]:
    term = query.lower()
    hits = [item for item in MOCK_LOCATIONS if term in item["name"].lower()]
    return sorted(hits, key=lambda x: (x["priority"], x["name"]))[:20]  # place ก่อน road แล้วเรียงชื่อ
