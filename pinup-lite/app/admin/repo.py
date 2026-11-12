# [ADAPTER] collection "datasets" + "features" (ข้อมูลขอบเขตการปกครอง)
# คืน feature เป็น dict {id, geometry, properties} — service ไม่ต้องรู้จัก _id
from pymongo.database import Database

_FIELDS = {"_id": 1, "geometry": 1, "properties": 1}


def _feature(doc: dict) -> dict:
    return {"id": str(doc["_id"]), "geometry": doc.get("geometry"), "properties": doc.get("properties", {})}


class BoundaryRepo:
    def __init__(self, db: Database):
        self.db = db

    def features_in_city(self, data_key: str, city_id: str) -> list[dict] | None:
        """dataset กลาง (ทุกเมือง) แล้วกรอง feature ตาม city_id. None = ไม่มี dataset"""
        dataset = self.db.datasets.find_one({"data_key": data_key})
        if not dataset:
            return None
        return [_feature(d) for d in self.db.features.find({"dataset_id": dataset["_id"], "city_id": city_id}, _FIELDS)]

    def features_of_city_dataset(self, data_key: str, city_id: str) -> list[dict] | None:
        """dataset ผูกกับเมืองอยู่แล้ว → เอา feature ทั้งหมดของ dataset. None = ไม่มี dataset"""
        dataset = self.db.datasets.find_one({"data_key": data_key, "city_id": city_id})
        if not dataset:
            return None
        return [_feature(d) for d in self.db.features.find({"dataset_id": dataset["_id"]}, _FIELDS)]
