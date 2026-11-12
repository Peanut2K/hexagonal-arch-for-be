# Hexagonal Lite — ฉบับย่อสำหรับ pinup-backend

ฉบับเต็ม (`../src`, `../FASTAPI.md`) มี domain / port / command / container / inbound-outbound แยกกันหมด
เหมาะกับทีมใหญ่ แต่ pinup-backend เป็น FastAPI ~4k บรรทัด, Mongo ตัวเดียว, ไม่มีแผนเปลี่ยน DB
→ เก็บไว้แค่ **ส่วนที่ได้ประโยชน์จริง**: แยก "logic" ออกจาก "Mongo" และ "HTTP" เพื่อให้ test ได้และอ่านง่าย

ตัวอย่างในโฟลเดอร์นี้คือ feature `projects` ของ pinup-backend จริง ย้ายมาเป็นโครงใหม่ (endpoint/response เหมือนเดิม)

## Tree

```
lite/
├── app/
│   ├── main.py              ← สร้าง app, include router, แปลง AppError → HTTP
│   ├── db.py                ← Mongo connection (lru_cache)
│   ├── errors.py            ← AppError, NotFound  (ไม่ import fastapi)
│   ├── projects/            ← 1 feature = 1 โฟลเดอร์
│   │   ├── router.py        [HTTP]    รับ/ส่ง, Depends(get_repo)
│   │   ├── schemas.py       [HTTP]    Pydantic request/response
│   │   ├── service.py       [CORE]    business logic — รับ repo เป็น parameter
│   │   └── repo.py          [ADAPTER] ที่เดียวที่แตะ pymongo/bson
│   └── sites/
│       └── analysis.py      [CORE]    analyze_polygon() — pure function (shapely + csv)
└── tests/
    └── test_projects_service.py   ← test service ด้วย FakeRepo ไม่ต้องมี Mongo
```

## กฎ 3 ข้อ (ทั้งหมดที่ต้องจำ)

1. **`service.py` ห้าม import `fastapi`, `pymongo`, `bson`** — error ใช้ `AppError`/`NotFound`, DB ใช้ผ่าน `repo`
2. **`repo.py` เป็นที่เดียวที่รู้จัก Mongo** — คืน `dict` ที่มี `"id": str` แล้ว ไม่ส่ง `_id`/`ObjectId` ออกไป
3. **`router.py` ไม่มี logic** — แปลง request → เรียก service → return

ทิศ import: `router → service → (repo ผ่าน parameter)`, `service → analysis`. ไม่มีย้อนกลับ

## ตัดอะไรออกจากฉบับเต็ม และทำไม

| ฉบับเต็ม | Lite | เหตุผล |
|---|---|---|
| `domain/model` dataclass แยก | ใช้ Pydantic `schemas.py` ตรง ๆ | shape ข้อมูลเท่ากับ API อยู่แล้ว แยกแล้วได้แค่ mapper ซ้ำ |
| Port (`Protocol`) | ไม่มี — `ProjectRepo` class เดียว, test ใช้ FakeRepo duck-typing | implementation เดียว + fake ใน test พอ |
| Command object | ส่ง request schema เข้า service เลย | field ตรงกัน 1:1 |
| `bootstrap/container.py` | `get_repo()` ใน `router.py` | 1 บรรทัดต่อ feature ไม่ต้องมีไฟล์กลาง |
| `adapters/inbound` / `outbound` | ชื่อไฟล์บอก layer (`router` / `repo`) | โฟลเดอร์ลึกโดยไม่ได้อะไรเพิ่ม |
| Layer-first (`domain/`, `application/`) | **Feature-first** (`projects/`, `sites/`) | เปิดโฟลเดอร์เดียวเห็นทั้ง feature |

**เพิ่มกลับเมื่อไหร่:** มี DB ตัวที่ 2 → ทำ `Protocol` ใน `service.py`, logic ซับซ้อนจน Pydantic ไม่พอ (state machine, invariant) → แยก domain dataclass ของ feature นั้น

## ย้าย pinup-backend มาใช้ (ทีละ feature ไม่ต้อง big-bang)

ตอนนี้ pinup: `routers/x.py → services/x_service.py (ใช้ db + HTTPException + ObjectId ตรง)`

1. สร้าง `app/x/` ย้าย `routers/x.py` → `router.py`, `schemas/x.py` → `schemas.py`
2. ดึงทุกบรรทัด `db.xxx.find/insert/update` + `ObjectId(...)` ใน service ไปเป็น method ใน `repo.py`
3. service: เปลี่ยน parameter `db: Database` → `repo: XRepo`, `HTTPException(404)` → `NotFound`
4. ฟังก์ชันคำนวณล้วน (เช่น `analyze_polygon_spatial` ใน `sites_service.py`) → `analysis.py` ไม่ต้องแก้ข้างใน
5. เพิ่ม `app.exception_handler(AppError)` ใน `main.py` (ครั้งเดียว)

เริ่มจาก `projects` + `sites` ก่อน (มี logic จริง) — `bdi`, `admin` ที่เป็นแค่อ่านข้อมูล ให้ router เรียก repo ตรงก็ได้

## สิ่งที่เจอใน pinup-backend ระหว่างดู (แก้ไปพร้อมกันได้)

- **`async def` + pymongo (sync)** → ทุก query block event loop ทั้งแอป. Lite ใช้ `def` ใน router แทน (FastAPI รันใน threadpool) — หรือเปลี่ยนไป `motor` (มีใน requirements แล้ว) ถ้าอยากคง async
- **service raise `HTTPException`** → service ผูกกับ FastAPI, test ยาก. Lite ใช้ `AppError` + handler ตัวเดียว (response ยังเป็น `{"detail": ...}` frontend ไม่ต้องแก้)
- **create project = insert site แล้วค่อย update `project_id`** (2 write) → lite insert site พร้อม `project_id` ทีเดียว
- **`list_projects` นับ site แบบ N+1** → คงไว้ แต่ย้ายมาอยู่ใน repo ที่เดียว เปลี่ยนเป็น `$lookup` ได้โดยไม่แตะ service
- **id ผิดรูปแบบ** เดิมได้ 400 `Invalid project_id`, lite ได้ 404 (repo คืน `None`) — อยากได้ 400 แบบเดิมให้ raise `AppError` ใน `_oid()`

## รัน test

```bash
cd lite
pip install fastapi pymongo pytest
python -m pytest tests
```
