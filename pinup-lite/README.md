# pinup-lite

`pinup-backend` ทั้งโปรเจกต์ ที่จัดโครงใหม่แบบ **Hexagonal Lite**
endpoint และ response เหมือนของเดิม (ตรวจแล้ว — ดูหัวข้อ [ตรวจแล้วว่าเหมือนเดิม](#12-ตรวจแล้วว่าเหมือนเดิม))
สิ่งที่เปลี่ยนคือ **โค้ดแต่ละบรรทัดไปอยู่ไฟล์ไหน และทำไม**

เอกสารนี้ตอบ 3 คำถาม:

1. ทำไมต้องแยก router / service / repo ออกจากกัน — และทำไมแยกแล้ว test ได้โดยไม่ต้องมี DB
2. แต่ละไฟล์ทำอะไร มีฟังก์ชันอะไร
3. ทำไม feature นี้มีไฟล์แค่เท่านี้ ทำไม feature นั้นมีมากกว่า

---

## สารบัญ

1. [สรุปใน 30 วินาที](#1-สรุปใน-30-วินาที)
2. [ทำไมต้องแยก — ปัญหาของโค้ดเดิม](#2-ทำไมต้องแยก--ปัญหาของโค้ดเดิม)
3. [แยกแล้ว test โดยไม่มี DB ได้ยังไง](#3-แยกแล้ว-test-โดยไม่มี-db-ได้ยังไง)
4. [โครงสร้างทั้งหมด](#4-โครงสร้างทั้งหมด)
5. [ตามรอย 1 request ตั้งแต่ต้นจนจบ](#5-ตามรอย-1-request-ตั้งแต่ต้นจนจบ)
6. [ไฟล์กลาง (ใช้ทั้งแอป)](#6-ไฟล์กลาง-ใช้ทั้งแอป)
7. [ทีละ feature](#7-ทีละ-feature)
8. [ทำไมแต่ละ feature มีไฟล์ไม่เท่ากัน](#8-ทำไมแต่ละ-feature-มีไฟล์ไม่เท่ากัน)
9. [กฎการ import ข้ามกัน](#9-กฎการ-import-ข้ามกัน)
10. [เพิ่ม feature ใหม่ / เขียน test](#10-เพิ่ม-feature-ใหม่--เขียน-test)
11. [ย้ายอะไรมาจากไหน + สิ่งที่เปลี่ยน](#11-ย้ายอะไรมาจากไหน--สิ่งที่เปลี่ยน)
12. [ตรวจแล้วว่าเหมือนเดิม](#12-ตรวจแล้วว่าเหมือนเดิม)
13. [รัน](#13-รัน)

---

## 1. สรุปใน 30 วินาที

**โฟลเดอร์ = feature, ไฟล์ = หน้าที่**

```
app/projects/
  router.py    [HTTP]     รับ request → เรียก service → ส่ง response   (ไม่มี logic)
  schemas.py   [HTTP]     รูปร่างข้อมูลเข้า-ออก (Pydantic)
  service.py   [CORE]     กฎและขั้นตอนของงาน                          (ไม่แตะ DB, ไม่แตะ HTTP)
  repo.py      [ADAPTER]  คุยกับ MongoDB                               (ที่เดียวที่รู้จัก pymongo)
```

**กฎ 3 ข้อ** — รักษาไว้ได้ ที่เหลือตามมาเอง:

1. `service.py` ห้าม import `fastapi`, `pymongo`, `bson`
2. `repo.py` เป็นที่เดียวที่รู้จัก MongoDB (ชื่อ collection, `_id`, `ObjectId`)
3. `router.py` ไม่มี logic — แค่ส่งต่อ

ป้ายที่ใช้ทั้งเอกสาร:

- **[HTTP]** ขอบนอกฝั่งหน้าเว็บ — รู้จัก FastAPI
- **[CORE]** แกนกลาง — กฎของธุรกิจ, ไม่รู้จักทั้ง HTTP และ DB
- **[ADAPTER]** ขอบนอกฝั่งของภายนอก — DB, อีเมล, crypto, API ภายนอก
- **[PURE]** ฟังก์ชันคำนวณล้วน — ใส่ input ได้ output, ไม่แตะอะไรเลย (เป็น CORE ชนิดหนึ่ง)

---

## 2. ทำไมต้องแยก — ปัญหาของโค้ดเดิม

### โค้ดเดิมหน้าตาแบบนี้

`pinup-backend/app/services/projects_service.py` (ตัดมาบางส่วน):

```python
from bson import ObjectId                 # ← รู้จัก Mongo
from fastapi import HTTPException         # ← รู้จัก HTTP
from pymongo.database import Database     # ← รู้จัก Mongo

async def get_project_by_id(project_id: str, db: Database):
    try:
        obj_id = ObjectId(project_id)                                  # ← เรื่อง Mongo
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid ...")    # ← เรื่อง HTTP

    project_doc = db.projects.find_one({"_id": obj_id})                # ← เรื่อง Mongo
    if not project_doc:
        raise HTTPException(status_code=404, detail=f"... not found")  # ← เรื่อง HTTP + กฎ

    site_docs = list(db.sites.find({"project_id": project_id}).sort("created_at", 1))  # ← Mongo
    ...
```

ฟังก์ชันเดียวทำ 3 เรื่องปนกัน: **กฎของงาน** (ไม่เจอ = error), **วิธีคุยกับ Mongo**, **วิธีตอบ HTTP**

### ปัญหาที่ตามมา

| ปัญหา                                    | เกิดจาก                                                                                               |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **test ไม่ได้ถ้าไม่มี MongoDB**          | ฟังก์ชันเรียก `db.projects.find_one` ตรง ๆ — จะ test ต้องมี Mongo จริง (หรือของจำลองทั้งก้อน)         |
| **test ไม่ได้ถ้าไม่มี FastAPI**          | ใช้ `HTTPException` — ผูก logic เข้ากับ web framework                                                 |
| **เปลี่ยน DB = แก้ทุก service**          | `db.xxx.find(...)` กระจายอยู่ในทุกไฟล์ service                                                        |
| **อ่านยาก**                              | 172 บรรทัดของ projects_service ส่วนใหญ่เป็น `try ObjectId / find_one / str(_id)` — กฎจริงจมอยู่ข้างใน |
| **โค้ดซ้ำ**                              | `try: ObjectId(x) except: raise HTTPException(400)` ซ้ำ 8 ที่ใน projects + sites                      |
| **แก้ feature เดียวต้องเปิด 3 โฟลเดอร์** | `routers/projects.py`, `services/projects_service.py`, `schemas/projects.py` อยู่คนละที่              |

### หลังแยก

`pinup-lite/app/projects/service.py`:

```python
def get_project(projects: ProjectRepo, sites: SiteRepo, project_id: str) -> dict:
    return {**_must_get(projects, project_id), "sites": sites.by_project(project_id)}

def _must_get(projects: ProjectRepo, project_id: str) -> dict:
    project = projects.get(project_id)
    if not project:
        raise NotFound(f"Project '{project_id}' not found")
    return project
```

เหลือแต่ **กฎ**: "เอา project มา ถ้าไม่มีให้ error แล้วแนบ site ของมัน"

- เรื่อง Mongo (`ObjectId`, `find_one`, `_id → id`) ย้ายไป `repo.py`
- เรื่อง HTTP (404) ย้ายไป `main.py` (แปลง `NotFound` → 404 ที่เดียว)
- เรื่องไฟล์กระจาย → รวมเป็นโฟลเดอร์ `projects/`

### แต่ละชิ้นที่แยกออกมา แยกเพื่ออะไร

| แยกอะไรออกมา                  | ไปไว้ที่                                        | เพื่อ                                                            |
| ----------------------------- | ----------------------------------------------- | ---------------------------------------------------------------- |
| คำสั่ง Mongo ทั้งหมด          | `x/repo.py`                                     | service test ได้โดยไม่มี DB, เปลี่ยน DB แก้ไฟล์เดียว             |
| `HTTPException`               | `errors.py` (`AppError`) + handler ใน `main.py` | service ไม่ผูก FastAPI, รูปแบบ error ทั้งแอปคุมจากที่เดียว       |
| request/response model        | `x/schemas.py`                                  | สัญญากับ frontend อยู่ที่เดียว เปิดดูได้ทันทีว่า API รับ-ส่งอะไร |
| สูตรคำนวณยาว ๆ                | `sites/analysis.py` ฯลฯ                         | ใช้ซ้ำได้หลายที่, test ง่ายสุด, ไม่บังขั้นตอนหลักใน service      |
| JWT / bcrypt / Google token   | `auth/security.py`                              | service อ่านเป็นภาษาธุรกิจ ไม่ต้องรู้จัก `jose`, `passlib`       |
| ส่งอีเมล                      | `auth/email.py`                                 | ตอน test แทนด้วยตัวปลอมได้ (ไม่ส่งเมลจริง)                       |
| ผูก "service ใช้ repo ตัวไหน" | `get_repo()` ใน `router.py`                     | จุดเดียวที่ต้องเปลี่ยนเมื่อจะสลับ repo (จริง ↔ ปลอม)             |

---

## 3. แยกแล้ว test โดยไม่มี DB ได้ยังไง

นี่คือหัวใจของทั้งโครงสร้าง อธิบายทีละขั้น

### ขั้นที่ 1: service ไม่สร้าง repo เอง — รับเข้ามาเป็น parameter

```python
# service.py
def create_project(projects: ProjectRepo, sites: SiteRepo, req) -> dict:
    project_id = projects.create(req.name, req.description)
    ...
```

service ไม่ได้เขียน `ProjectRepo(get_db())` เอง มันแค่บอกว่า "ส่ง repo มาให้ฉันด้วย"
ใครเรียก service คนนั้นเลือกว่าจะส่ง repo ตัวไหนมา (เทคนิคนี้ชื่อ **dependency injection** — ฟังดูหรู แต่จริง ๆ คือ "ส่งของเข้าไปทาง parameter")

### ขั้นที่ 2: ตอนรันจริง router ส่ง repo จริง

```python
# router.py
def get_project_repo(db: Database = Depends(get_db)) -> ProjectRepo:
    return ProjectRepo(db)                       # ← repo ที่ต่อ Mongo จริง

@router.post("")
def create_project(body, projects: ProjectRepo = Depends(get_project_repo), sites = Depends(get_site_repo)):
    return service.create_project(projects, sites, body)
```

### ขั้นที่ 3: ตอน test เราส่ง repo ปลอม

```python
# tests/test_projects_service.py
class FakeProjects:                    # ไม่ต่อ DB — เก็บใน dict ธรรมดา
    def __init__(self):
        self.rows = {}
    def create(self, name, description):
        pid = f"p{len(self.rows) + 1}"
        self.rows[pid] = {"id": pid, "name": name, ...}
        return pid
    def get(self, pid):
        return self.rows.get(pid)
    ...

def test_sites_are_numbered_per_project():
    projects, sites = FakeProjects(), FakeSites()
    p = service.create_project(projects, sites, ProjectCreateRequest(name="บางนา", geometry=GEOM))
    p = service.add_site_to_project(projects, sites, p["id"], AddSiteToProjectRequest(geometry=GEOM))
    assert [s["name"] for s in p["sites"]] == ["Site 1 (บางนา)", "Site 2 (บางนา)"]
```

### ทำไม service ยอมรับของปลอม?

Python ไม่เช็คว่า object เป็น class อะไร — เช็คแค่ว่า **มี method ที่เรียกไหม** (เรียกว่า _duck typing_: "เดินเหมือนเป็ด ร้องเหมือนเป็ด ก็คือเป็ด")
service เรียก `projects.create(...)` และ `projects.get(...)` → `FakeProjects` มีสองอันนี้ → ทำงานได้

### ทำไมต้องรักษากฎ "service ห้าม import pymongo"?

ถ้า service แอบเรียก `db.projects.find_one(...)` ตรง ๆ แม้แต่บรรทัดเดียว — FakeRepo ช่วยอะไรไม่ได้ เพราะบรรทัดนั้นไม่ได้ผ่าน repo
**กฎข้อ 1 คือสิ่งที่ทำให้ "ทุกการแตะ DB ต้องผ่าน repo" เป็นจริง** → แทน repo ได้ = แทน DB ได้ทั้งหมด

ใน `service.py` จะเห็น import แบบนี้:

```python
if TYPE_CHECKING:  # ใช้แค่ type hint — runtime ไม่ import pymongo
    from app.projects.repo import ProjectRepo
```

`TYPE_CHECKING` เป็น `False` ตอนรันจริง → บรรทัดนี้ไม่ถูก execute → service ไม่ลาก pymongo เข้ามาโดยอ้อม แต่ editor ยังรู้ type ให้ autocomplete

### ของภายนอกอื่นที่ไม่ใช่ DB — แทนยังไง?

| ของภายนอก                                | ใน test แทนด้วย                                                       |
| ---------------------------------------- | --------------------------------------------------------------------- |
| MongoDB                                  | FakeRepo (ส่งเข้าทาง parameter)                                       |
| อ่าน BDI CSV (`analyze_polygon_spatial`) | `monkeypatch.setattr(sites_service, "analyze_polygon_spatial", fake)` |
| ส่งอีเมล                                 | `monkeypatch.setattr(auth_service, "send_verification_email", fake)`  |
| ทั้ง route ผ่าน HTTP                     | `app.dependency_overrides[get_project_repo] = lambda: FakeProjects()` |

`monkeypatch` = ของ pytest ที่ "สลับฟังก์ชันชั่วคราวระหว่าง test" แล้วคืนของเดิมให้เมื่อ test จบ

### ผลลัพธ์

```
$ python -m pytest tests
2 passed in 0.31s
```

ไม่ต้องเปิด MongoDB, ไม่ต้องมี `.env`, ไม่ต้องรัน server — 0.3 วินาที

---

## 4. โครงสร้างทั้งหมด

```
pinup-lite/
├── app/
│   ├── main.py                    [HTTP]     จุดเริ่มแอป
│   ├── config.py                             ค่าจาก env + path
│   ├── db.py                      [ADAPTER]  เปิด Mongo connection
│   ├── errors.py                  [CORE]     AppError และลูก ๆ
│   │
│   ├── shared/                               ใช้ร่วมกันหลาย feature
│   │   ├── mongo.py               [ADAPTER]  helper ของ repo ทุกตัว
│   │   └── geo/                   [PURE]     อ่าน CSV, GeoJSON, คำนวณพื้นที่
│   │
│   ├── projects/   router · schemas · service · repo
│   ├── sites/      router · schemas · service · repo · analysis · zoning_mapping · zoning_rules · risk
│   ├── auth/       router · schemas · service · repo · security · email
│   ├── admin/      router · service · repo
│   ├── places/     router · schemas · service
│   ├── transit/    router · schemas · service · loader · data/
│   ├── search/     router · schemas · service · mock_data
│   ├── ai_chat/    router · schemas · service · tfidf
│   └── bdi/        router
│
├── bdi-data/                      CSV ของ BDI (area, land, street, building-footprint)
├── tests/
│   └── test_projects_service.py
├── requirements.txt, Dockerfile, docker-compose.yml, Makefile, vercel.json   (เหมือนเดิม)
```

---

## 5. ตามรอย 1 request ตั้งแต่ต้นจนจบ

ผู้ใช้กด **"Add to project +"** → frontend ส่ง:

```
POST /api/projects/6650.../sites
{"geometry": {"type": "Polygon", "coordinates": [...]}}
```

```
① main.py
   URL ขึ้นต้น /api/projects → ส่งให้ projects router

② projects/router.py :: add_site_to_project
   - FastAPI ใช้ schemas.AddSiteToProjectRequest ตรวจ body
     (ไม่มี geometry → ตอบ 422 ทันที ไม่ถึง service)
   - เรียก get_project_repo() + get_site_repo() → ได้ repo จริง 2 ตัว
   - เรียก service.add_site_to_project(projects, sites, project_id, body)

③ projects/service.py :: add_site_to_project
   - _must_get(projects, id) → projects.get(id)
         ↳ projects/repo.py: oid() แปลง id → find_one → out() แปลง _id → id
         ↳ ไม่เจอ → raise NotFound
   - ตั้งชื่อ: "Site {จำนวนเดิม+1} ({ชื่อ project})"  ← กฎของงาน
         ↳ sites.count_by_project(id)  (sites/repo.py)
   - sites_service.analyze_and_save(sites, geometry, name, project_id)   ← ข้าม feature ผ่าน service

④ sites/service.py :: analyze_and_save
   - analyze_polygon_spatial(geometry)      ← sites/analysis.py (PURE)
         ↳ อ่าน bdi-data/*.csv, หา zoning, ถนนใกล้สุด, ความเสี่ยง, FAR/OSR/GFA
   - sites.insert(...)                       ← sites/repo.py → db.sites.insert_one

⑤ กลับมาที่ projects/service.py
   - projects.touch(id)                      ← อัปเดต updated_at
   - return get_project(...)                 ← project + site ทั้งหมด

⑥ projects/router.py
   - FastAPI จัดรูป dict ด้วย schemas.ProjectResponse → JSON กลับ frontend
```

ถ้าเกิด `NotFound` ที่ขั้น ③ → กระโดดไป `main.py :: app_error_handler` → ตอบ `404 {"detail": "Project '...' not found"}`
ถ้า id ผิดรูปแบบ → `shared/mongo.py :: oid()` raise `AppError` → ตอบ `400 {"detail": "Invalid project_id: ..."}`

---

## 6. ไฟล์กลาง (ใช้ทั้งแอป)

### `app/main.py` — จุดเริ่มแอป (44 บรรทัด)

- `load_dotenv()` **ต้องอยู่บรรทัดแรก** เพราะ `config.py` และ `auth/security.py` อ่าน env ตอน import
- ตั้ง CORS (เปิดหมดเหมือนเดิม)
- `include_router` ทุก feature ใต้ `/api` (search อยู่ใต้ `/api/search`)
- `app_error_handler` — **ที่เดียวที่แปลง `AppError` เป็น HTTP response**
  - ใช้ key `"detail"` เหมือน `HTTPException` เดิม → frontend ไม่ต้องแก้
  - ถ้าเป็น `Unauthorized` เติม header `WWW-Authenticate: Bearer` ให้ (มาตรฐาน OAuth2)
- `GET /` ข้อความต้อนรับ

### `app/config.py` — ค่าตั้งค่า (16 บรรทัด)

- `ROOT`, `BDI_DATA_DIR` — path ของโปรเจกต์และโฟลเดอร์ CSV (ใช้ `pathlib` แทน `os.path.dirname` ซ้อน 3 ชั้น)
- `MONGO_URI`, `DB_NAME`, `GOOGLE_MAPS_API_KEY` จาก env
- `require_google_maps_api_key()` — คืน key หรือ raise ถ้าไม่ได้ตั้ง (transit ใช้)
- ตัด `DATA_ROOT` / `TARGET_CITIES` ของเดิมทิ้ง — ไม่มีใครในแอปใช้ (ใช้แค่ใน `database/old_script`)

### `app/db.py` — Mongo connection (16 บรรทัด) [ADAPTER]

- `get_db()` — สร้าง `MongoClient` **ครั้งเดียว** (`@lru_cache` จำผลไว้) แล้วคืน database เดิมทุกครั้ง
- สร้าง index `sites.project_id` ตอนต่อครั้งแรก (เหมือนเดิม)
- แทน 3 ไฟล์เดิม: `db/database.py` (global variable), `dependencies.py` (generator ที่ไม่ได้ทำอะไร), ส่วนหนึ่งของ `core/config.py`

### `app/errors.py` — error ทางธุรกิจ (22 บรรทัด) [CORE]

```python
class AppError(Exception):   status = 400   # ทั่วไป / ข้อมูลไม่ถูก
class NotFound(AppError):    status = 404
class Unauthorized(AppError):status = 401
class Forbidden(AppError):   status = 403
```

- service ใช้ `raise NotFound("...")` แทน `raise HTTPException(404, ...)`
- ไฟล์นี้ **ไม่ import fastapi** → service ที่ใช้ยังเป็นอิสระจาก HTTP
- status code อื่น ๆ (502, 503) ส่งเป็น parameter: `AppError("Google error", status=502)`
- ทำไมมี `status` อยู่ใน error ทั้งที่บอกว่าไม่ผูก HTTP? → ประนีประนอม: แยก mapping ออกไปอีกไฟล์ก็ได้ แต่สำหรับ 4 คลาส ไม่คุ้ม

### `app/shared/mongo.py` — helper ของ repo (20 บรรทัด) [ADAPTER]

- `oid(value, label)` — แปลง string → `ObjectId`; ผิดรูปแบบ → `AppError("Invalid {label}: ...")`
  แทนบล็อก `try: ObjectId(x) except: raise HTTPException(400)` ที่เคยซ้ำ 8 ที่
- `out(doc)` — แปลง Mongo doc เป็น dict ธรรมดา: `_id` (ObjectId) → `id` (str)
  **ทำให้ service ไม่เคยเห็น `_id`** — ถ้าวันหนึ่งเปลี่ยนเป็น Postgres ที่ id เป็นตัวเลข service ก็ไม่ต้องรู้
- **service ห้าม import ไฟล์นี้** (มี bson)

### `app/shared/geo/` — เครื่องมือ geo [PURE]

อยู่ใน `shared/` เพราะใช้ **มากกว่า 1 feature** (sites + bdi)

| ไฟล์                          | ทำอะไร                                                                   | ใครใช้              |
| ----------------------------- | ------------------------------------------------------------------------ | ------------------- |
| `area_calculator.py`          | `calculate_area_m2/km2` — แปลงพิกัด WGS84 → UTM แล้วคำนวณพื้นที่จริง     | sites/analysis      |
| `load_csv_with_geo.py`        | อ่าน CSV + parse คอลัมน์ `GEO_COOR` (สลับ lon/lat ได้)                   | sites/analysis      |
| `load_csv_as_geojson.py`      | อ่าน CSV → GeoJSON FeatureCollection (ซ่อม polygon, กรอง vertex ผิดปกติ) | bdi/router          |
| `parse_malformed_geo_json.py` | parse ข้อความพิกัดที่รูปแบบเพี้ยนใน CSV                                  | 2 ไฟล์ข้างบน        |
| `repair_polygon_rings.py`     | ซ่อม ring ที่ตัดกันเอง, หา vertex ที่หลุดไกล                             | load_csv_as_geojson |
| `swap_lon_lat.py`             | สลับ `[lon, lat]` ↔ `[lat, lon]`                                         | load_csv_with_geo   |

ย้ายมาจาก `utils/` โดย **ไม่แก้เนื้อใน** — แก้แค่ path import

---

## 7. ทีละ feature

### 7.1 `projects/` — โปรเจกต์ (กลุ่มของแปลงที่ดิน)

**ทำไมมีครบ 4 ไฟล์:** มี DB (collection `projects`) + มีกฎ (ตั้งชื่อ site, ลบ project ต้องลบ site ด้วย)

| ไฟล์                          | หน้าที่               | ข้างในมี                                                                                                                                                                                                                       |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `router.py` [HTTP] 45 บรรทัด  | 5 endpoint            | `get_project_repo()` สร้าง `ProjectRepo` จาก db · `create_project` · `add_site_to_project` · `list_projects` · `get_project` · `delete_project` · ตัวย่อ `Projects = Depends(...)` / `Sites = Depends(...)` กันบรรทัดยาว       |
| `schemas.py` [HTTP] 74 บรรทัด | สัญญากับ frontend     | `ProjectCreateRequest` (name, geometry, description) · `AddSiteToProjectRequest` (geometry, name?) · `ProjectListItem` (มี `site_count`) · `ProjectResponse` (มี `sites: list[SiteResponse]`) · มีตัวอย่าง JSON สำหรับ Swagger |
| `service.py` [CORE] 51 บรรทัด | กฎ                    | ดูข้างล่าง                                                                                                                                                                                                                     |
| `repo.py` [ADAPTER] 42 บรรทัด | collection `projects` | `create` · `get` · `list` (เรียงใหม่สุดก่อน) · `touch` (อัปเดต `updated_at`) · `delete` · `_project()` เติมค่า default ให้ doc เก่าที่ field ไม่ครบ                                                                            |

**กฎใน `service.py`:**

- `create_project` — สร้าง project แล้ว **ต้องมี site แรกเสมอ** ชื่อ `"Site 1 ({ชื่อ project})"`
- `add_site_to_project` — project ต้องมีอยู่จริง · ไม่ระบุชื่อ → `"Site {n+1} ({ชื่อ project})"` · อัปเดตเวลาของ project
- `list_projects` — แนบ `site_count` ให้ทุก project
- `get_project` — project + site ทั้งหมด (เรียงเก่าไปใหม่)
- `delete_project` — ไม่เจอ → 404 · เจอ → ลบ site ของมันทั้งหมดด้วย
- `_must_get` — ดึงหรือ raise `NotFound` (ใช้ซ้ำ 2 ที่)

**ทำไม service รับ repo 2 ตัว:** site อยู่คนละ collection และ **เป็นของ feature sites** — projects ไม่ไปยุ่ง collection `sites` เอง แต่ใช้ `SiteRepo` ของ sites
**ทำไมไม่มี `analysis.py`:** projects ไม่มีสูตรคำนวณของตัวเอง — การวิเคราะห์ polygon เป็นงานของ sites

### 7.2 `sites/` — แปลงที่ดิน + วิเคราะห์ผังเมือง

**ทำไมมีไฟล์เยอะที่สุด:** เป็น feature ที่มี **logic หนักที่สุด** (วิเคราะห์ zoning, ถนน, ความเสี่ยง) ทุกไฟล์เพิ่มเป็นกฎผังเมืองแบบ PURE ที่ใช้แค่ sites → อยู่ใน sites ไม่ใช่ shared

| ไฟล์                          | หน้าที่                     | ข้างในมี                                                                                                                                                                                                                                                                                                                              |
| ----------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `router.py` [HTTP] 33         | 4 endpoint                  | `get_site_repo()` (projects ก็ยืมใช้) · `analyze_site` · `get_site` · `update_site` · `delete_site`                                                                                                                                                                                                                                   |
| `schemas.py` [HTTP] 64        | สัญญา                       | `SiteAnalyzeRequest` · `SiteAnalysis` (25 field: zoning, ที่อยู่, ถนน, ความเสี่ยง, FAR/OSR/GFA) · `ZoningRegulationItem` · `CadastralRow` · `SiteResponse`                                                                                                                                                                            |
| `service.py` [CORE] 44        | ขั้นตอน                     | `analyze_and_save` (วิเคราะห์ → บันทึก, **projects เรียกตัวนี้**) · `create_site` · `get_site` · `update_site` (วิเคราะห์ใหม่ทุกครั้งที่แก้) · `delete_site`                                                                                                                                                                          |
| `repo.py` [ADAPTER] 53        | collection `sites`          | `insert` · `get` · `update` (คืน doc หลังแก้ด้วย `find_one_and_update`) · `delete` · `by_project` · `count_by_project` · `delete_by_project`                                                                                                                                                                                          |
| `analysis.py` [PURE] 184      | **สมองของ sites**           | `analyze_polygon_spatial(geometry) → SiteAnalysis` ทำ 5 ขั้น ① หา zoning จาก area.csv ② หาที่อยู่/สถานะที่ดินจาก land.csv ③ หาถนนใกล้สุดในรัศมี 500 ม. (ถนนใหญ่ก่อนซอย) จาก street.csv ④ ดึงข้อบังคับการใช้ที่ดิน ⑤ ประเมินความเสี่ยง · helper: `extract_address_components` · `fetch_zoning_regulations` · `row_to_shapely_geometry` |
| `zoning_mapping.py` [PURE] 65 | ตาราง zoning                | `normalize_zoning_code` (เลขไทย→อารบิก, จัดรูปรหัส) · `get_zoning_info` → ชื่อ, FAR, OSR                                                                                                                                                                                                                                              |
| `zoning_rules.py` [PURE] 311  | ข้อบังคับผังเมือง กทม. 2556 | `get_main_zoning_regulations(code)` → กิจกรรมที่อนุญาต/มีเงื่อนไข                                                                                                                                                                                                                                                                     |
| `risk.py` [PURE] 71           | ความเสี่ยงภูมิศาสตร์        | `evaluate_geographic_risks(เขต, แขวง, จังหวัด)` → น้ำท่วม, ดินถล่ม, ดินทรุด                                                                                                                                                                                                                                                           |

**ทำไมแยก `analysis.py` ออกจาก `service.py`:**

- **service** = ผู้คุมขั้นตอน: ใช้ repo, มีผลข้างเคียง (บันทึก/ลบ), raise error
- **analysis** = เครื่องคิดเลข: polygon เข้า → ผลวิเคราะห์ออก, ไม่บันทึกอะไร, ใส่ input เดิมได้ผลเดิมเสมอ
- มี 3 ที่เรียกใช้ (สร้าง site, แก้ site, เพิ่ม site ใน project) — ถ้าฝังใน service จะต้องก๊อปหรือ import วน
- 184 บรรทัด — ถ้าอยู่ใน service จะมองไม่เห็นขั้นตอนหลัก 5 บรรทัด

**ทำไม `repo.py` ของ sites มี method `by_project` / `count_by_project` / `delete_by_project`:** projects ต้องใช้ แต่ collection `sites` เป็นของ sites → sites เป็นคนเปิดช่องให้ (projects ไม่เขียน query `db.sites` เอง)

### 7.3 `auth/` — สมาชิก / login

**ทำไมมี 6 ไฟล์:** มี DB + มีของภายนอก 2 อย่างที่ไม่ใช่ DB (crypto, อีเมล) → แยกเป็น adapter คนละไฟล์

| ไฟล์                       | หน้าที่                         | ข้างในมี                                                                                                                                                                                                                                                                                               |
| -------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `router.py` [HTTP] 74      | 10 endpoint + **ตัวตรวจ login** | `oauth2_scheme` (อ่าน `Authorization: Bearer ...`) · `get_repo` · **`get_current_user`** — dependency ที่ route ไหนต้อง login ก็ใส่ `user = Depends(get_current_user)` · register · login · google-login · forgot/reset-password · verify-email · resend-verification · me · profile · change-password |
| `schemas.py` [HTTP] 64     | สัญญา                           | `UserCreate` · `Token` · `User` (response ของ /me) · `UserUpdate` · request ของแต่ละ flow (email ใช้ `EmailStr` ตรวจรูปแบบให้)                                                                                                                                                                         |
| `service.py` [CORE] 160    | กฎ                              | ดูข้างล่าง                                                                                                                                                                                                                                                                                             |
| `repo.py` [ADAPTER] 22     | collection `users`              | `find_by_email` · `insert` · `update` (ค้นด้วย email ซึ่ง unique → service ไม่ต้องถือ `_id`)                                                                                                                                                                                                           |
| `security.py` [ADAPTER] 49 | crypto ทั้งหมด                  | `verify_password` / `get_password_hash` (bcrypt) · `create_access_token` / `read_token` (JWT) · `verify_google_token` · ค่าคงที่ `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE`                                                                                                                                   |
| `email.py` [ADAPTER] 86    | ส่งเมล                          | `send_verification_email` · `send_forgot_password_email` (HTML template + ลิงก์กลับ frontend)                                                                                                                                                                                                          |

**กฎใน `service.py`:**

- `register_user` — email ซ้ำไม่ได้ · สร้าง user `is_verified=False` · ส่งเมลยืนยัน (token อายุ 24 ชม.)
- `login` — รหัสผิด → 401 · ยังไม่ยืนยันเมล → 403 · ผ่าน → token อายุ 30 นาที
- `google_login` — user ใหม่ → สร้าง · user เดิมที่ยังไม่ผูก Google → ผูกให้
- `forgot_password` — ส่ง token รีเซ็ต (อายุ 15 นาที)
- `reset_password` / `verify_email` — token ต้องเป็น **ประเภทที่ถูกต้อง** (`reset` / `verification`) กันเอา token ประเภทอื่นมาใช้
- `resend_verification` — ไม่มี email นี้ก็ตอบ "ส่งแล้ว" (**กัน email enumeration** — คนนอกเดาไม่ได้ว่า email ไหนสมัครไว้)
- `update_profile` — แก้เฉพาะ field ที่ส่งมาและไม่ใช่ null
- `change_password` — ต้องใส่รหัสเดิมถูก
- `current_user` — token ต้องถูก, ไม่ใช่ token reset/verification, และ user ต้องมีอยู่ → ไม่งั้น 401

**ทำไม `get_current_user` อยู่ใน router ไม่ใช่ service:** มันอ่าน header HTTP (`OAuth2PasswordBearer`) = เรื่อง HTTP → อยู่ router แต่ **กฎ** ว่า token แบบไหนใช้ได้ อยู่ใน `service.current_user`
**ทำไมบาง route เป็น `async def` บางอันเป็น `def`:** 3 route ที่ส่งเมล (register, forgot, resend) ต้อง `await` → ต้อง async ส่วนที่เหลือใช้ `def` เพื่อให้ pymongo (sync) ไปรันใน threadpool ไม่ block แอป (ดู [หัวข้อ 11](#11-ย้ายอะไรมาจากไหน--สิ่งที่เปลี่ยน))

### 7.4 `admin/` — ขอบเขตการปกครอง (เทศบาล, ตำบล, อำเภอ, จังหวัด, เขต)

**ทำไมไม่มี `schemas.py`:** response เป็น GeoJSON ที่ properties ต่างกันทุก endpoint และไม่มี request body → ไม่มีอะไรให้ประกาศ (เดิมก็ไม่มี)

| ไฟล์                    | หน้าที่                             | ข้างในมี                                                                                                                                                                                                   |
| ----------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `router.py` [HTTP] 43   | 6 endpoint `/api/{city_id}/bound-*` | แต่ละตัว 1 บรรทัด                                                                                                                                                                                          |
| `service.py` [CORE] 110 | จัดรูป properties                   | `_collection()` ห่อเป็น FeatureCollection + raise `NotFound` ถ้าไม่มี dataset · 6 ฟังก์ชันที่ต่างกันแค่ `fmt()` (เลือก field, ทำชื่อสองภาษา, ปัดเศษ) · `_district_fmt()` ใช้ร่วมระหว่างเขต กทม. กับปริมณฑล |
| `repo.py` [ADAPTER] 28  | collection `datasets` + `features`  | `features_in_city` (dataset กลาง กรอง feature ตามเมือง) · `features_of_city_dataset` (dataset ผูกเมืองอยู่แล้ว) · คืน `None` = ไม่มี dataset                                                               |

**เดิม 262 บรรทัด เหลือ 110 + 28:** ของเดิมมี 6 ฟังก์ชันที่ query DB เหมือนกันเป๊ะ ต่างแค่การจัด properties พอแยก query ไป repo ก็เห็นชัดว่ามี query แค่ 2 แบบ ส่วนที่ต่างจริง ๆ เหลือแค่ `fmt()`

### 7.5 `places/` — รายละเอียดสถานที่จาก Google Places

**ทำไมไม่มี `repo.py`:** ไม่มี DB — ข้อมูลมาจาก Google API

| ไฟล์                   | หน้าที่                                                                                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `router.py` [HTTP] 26  | `GET /api/places/details?query=...` หรือ `?place_id=...` · เช็คว่าส่งมา**อย่างใดอย่างหนึ่ง**เท่านั้น (422) — เป็นการตรวจรูปแบบ input จึงอยู่ router               |
| `schemas.py` [HTTP] 21 | `PlaceDetailResponse` (ชื่อ, ที่อยู่, พิกัด, รูป, เวลาเปิด ฯลฯ)                                                                                                   |
| `service.py` 178       | `get_place_details` ค้นด้วยชื่อหรือ id → ดึงรูปพร้อมกันสูงสุด 6 รูป (`asyncio.gather`) → จัดรูป · `_resolve_type` แปลงประเภทสถานที่เป็นภาษาไทย · `_resolve_photo` |

**ข้อควรรู้ (ตรงไปตรงมา):** `service.py` นี้เรียก `httpx` ไปหา Google ตรง ๆ = service กับ adapter รวมอยู่ไฟล์เดียว
ยอมรับได้เพราะ logic ทั้งหมดคือ "แปลงผลจาก Google" ถ้าวันหนึ่งอยาก test โดยไม่ยิง Google จริง → แยกส่วน `httpx` ออกเป็น `places/google_client.py` แล้วส่งเข้า service แบบเดียวกับ repo

### 7.6 `transit/` — สถานีขนส่งใกล้เคียง (BTS/MRT/BRT/เรือ/รถเมล์)

**ทำไมมี `loader.py` + `data/`:** มีข้อมูลสถานีแบบไฟล์ JSON (ไม่ได้อยู่ใน DB) ใช้แค่ transit → อยู่ใน transit

| ไฟล์                     | หน้าที่                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `router.py` [HTTP] 20    | `GET /api/transit/nearby-stations?lat&lng&radius&transport_type` · ตรวจช่วงพิกัด/รัศมีด้วย `Query(ge=, le=)`                                                                                                       |
| `schemas.py` [HTTP] 24   | `TransitStation` (ชื่อ, ระบบ, สาย, รหัสสถานี, ระยะทาง) · `NearbyTransitStationsResponse`                                                                                                                           |
| `service.py` 334         | `get_nearby_stations`: ค้น Google Places รอบจุด → จับคู่กับข้อมูลสถานีของเราด้วยชื่อ/alias → ระบุระบบ (BTS/MRT/…) → ตัดสถานีซ้ำ (ทางเข้า 1, 2, 3 ของสถานีเดียวกัน) → เรียงตามระยะ · มี helper `_` นำหน้าอีก 16 ตัว |
| `loader.py` [ADAPTER] 77 | อ่าน `data/*.json` ครั้งเดียว (`lru_cache`) สร้าง lookup table · `normalize_text` ทำชื่อให้เทียบกันได้ (ตัดคำว่า station/bts/mrt, ตัดวรรณยุกต์)                                                                    |
| `data/`                  | `stations.json` · `bus_stops.json` · `transit_aliases.json` · `transport_type_aliases.json`                                                                                                                        |

ข้อควรรู้เดียวกับ places: service เรียก Google ตรง

### 7.7 `search/` — ค้นหาสถานที่ (ช่องค้นหา)

**ทำไมเล็กที่สุดในกลุ่มที่มี service:** ตอนนี้ค้นจาก **mock data** ในไฟล์ ไม่มี DB ไม่มี API

| ไฟล์                   | หน้าที่                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `router.py` [HTTP] 12  | `GET /api/search/?q=...`                                           |
| `schemas.py` [HTTP] 13 | `SearchResultItem` (ชื่อ, ประเภท place/road, priority, พิกัด)      |
| `service.py` [CORE] 8  | กรองชื่อที่มีคำค้น → เรียง place ก่อน road แล้วตามชื่อ → 20 อันแรก |
| `mock_data.py` 92      | `MOCK_LOCATIONS` รายการสถานที่ตัวอย่าง                             |

**ทำไมยังมี `service.py` ทั้งที่แค่ 8 บรรทัด:** มี **กฎ** (เรียง place ก่อน road, จำกัด 20) และวันที่เปลี่ยนจาก mock เป็น DB จริง → เพิ่ม `repo.py` แล้วแก้ service ไม่กี่บรรทัด router ไม่ต้องแตะ

### 7.8 `ai_chat/` — แชตถามกฎผังเมือง (RAG + Typhoon LLM)

| ไฟล์                  | หน้าที่                                                                                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `router.py` [HTTP] 52 | ask · history · clear-history · sessions · คำอธิบาย endpoint                                                                                                |
| `schemas.py` [HTTP] 7 | `Question` (question, additional_context, session_id) — เดิมประกาศอยู่ใน router                                                                             |
| `service.py` 158      | `process_chat_request`: ตรวจคำถาม → หา chunk ที่เกี่ยวข้องจากเอกสารผังเมือง (TF-IDF + fuzzy) → ส่งให้ Typhoon ตอบ → เก็บประวัติ 10 ข้อความล่าสุดต่อ session |
| `tfidf.py` [PURE] 22  | `ThaiTfidf` — ค้นข้อความไทยด้วย character n-gram                                                                                                            |

**ข้อควรรู้:** ย้ายโครงอย่างเดียว ไม่ได้แก้ logic:

- session เก็บใน memory → หายเมื่อ restart, ไม่แชร์ระหว่าง server หลายตัว
- router อ่าน `conversation_sessions` ของ service ตรง ๆ (ควรผ่านฟังก์ชัน)
- เรียก OpenAI client แบบ sync ใน `async def` → block แอประหว่างรอ LLM

ถ้าจะทำให้เป็น lite เต็มตัว: เพิ่ม `repo.py` เก็บ session ใน Mongo + แยก `typhoon_client.py`

### 7.9 `bdi/` — ส่งข้อมูล BDI เป็น GeoJSON

**ทำไมมีแค่ `router.py`:** ทั้ง feature คือ "อ่าน CSV → ส่งกลับ" ไม่มีกฎ ไม่มี DB
สร้าง service ที่ทำแค่ `return load_csv_as_geojson(...)` = เพิ่มไฟล์โดยไม่ได้อะไร

| endpoint                      | ไฟล์ CSV               | หมายเหตุ                                                              |
| ----------------------------- | ---------------------- | --------------------------------------------------------------------- |
| `/api/bdi/area`               | area.csv               | `skip_repair=True` — polygon zoning ใหญ่หลายกิโลได้ (ตรวจด้วยมือแล้ว) |
| `/api/bdi/land`               | land.csv               |                                                                       |
| `/api/bdi/street`             | street.csv             |                                                                       |
| `/api/bdi/building-footprint` | building-footprint.csv |                                                                       |

---

## 8. ทำไมแต่ละ feature มีไฟล์ไม่เท่ากัน

**ไม่มีกฎว่าทุก feature ต้องมีครบ** — มีไฟล์เมื่อมีเหตุผล ถามตามลำดับนี้:

```
มี logic / กฎของงานไหม?
├─ ไม่มี (แค่ส่งของต่อ)                         → router.py อย่างเดียว           (bdi)
└─ มี → service.py
        │
        ├─ มี request/response ที่ต้องประกาศไหม? → schemas.py                     (เกือบทุกตัว ยกเว้น admin, bdi)
        │
        ├─ ใช้ DB ไหม?                          → repo.py                        (projects, sites, auth, admin)
        │
        ├─ มีสูตรคำนวณยาว/ใช้ซ้ำหลายที่ไหม?      → analysis.py หรือไฟล์ PURE      (sites)
        │
        ├─ ใช้ของภายนอกอื่น (crypto, เมล, API)?  → ไฟล์ adapter แยก               (auth: security, email)
        │
        └─ มีข้อมูลไฟล์/ข้อมูลคงที่?              → loader / mock_data / data/     (transit, search)
```

| feature  | router | schemas | service | repo | อื่น ๆ                    | เหตุผลหลัก              |
| -------- | :----: | :-----: | :-----: | :--: | ------------------------- | ----------------------- |
| projects |   ✓    |    ✓    |    ✓    |  ✓   |                           | DB + กฎ                 |
| sites    |   ✓    |    ✓    |    ✓    |  ✓   | analysis, zoning ×2, risk | DB + logic หนักที่สุด   |
| auth     |   ✓    |    ✓    |    ✓    |  ✓   | security, email           | DB + crypto + อีเมล     |
| admin    |   ✓    |         |    ✓    |  ✓   |                           | DB + จัดรูป, ไม่มี body |
| places   |   ✓    |    ✓    |    ✓    |      |                           | API ภายนอก ไม่มี DB     |
| transit  |   ✓    |    ✓    |    ✓    |      | loader, data/             | API ภายนอก + JSON       |
| search   |   ✓    |    ✓    |    ✓    |      | mock_data                 | mock, ไม่มี DB          |
| ai_chat  |   ✓    |    ✓    |    ✓    |      | tfidf                     | LLM + memory            |
| bdi      |   ✓    |         |         |      |                           | ไม่มี logic             |

**ไฟล์ไปอยู่ไหน — `x/` หรือ `shared/`?**
ใช้ feature เดียว → อยู่ใน feature นั้น (เช่น `zoning_rules.py` อยู่ใน sites)
ใช้ ≥ 2 feature → `shared/` (เช่น `load_csv_with_geo` ใช้ทั้ง sites และ bdi)
อย่าย้ายเข้า `shared/` "เผื่ออนาคต" — ย้ายเมื่อมีคนที่ 2 ใช้จริง

---

## 9. กฎการ import ข้ามกัน

```
router.py  ──▶  service.py  ──▶  analysis.py / ไฟล์ PURE
   │               │
   │               └──▶  errors.py
   └──▶  repo.py (แค่สร้างแล้วส่งให้ service)

repo.py  ──▶  shared/mongo.py, db.py
```

| จาก → ไป                                             | ได้ไหม                                  | ตัวอย่าง                                              |
| ---------------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| router → service, schemas, repo                      | ✓                                       | ปกติ                                                  |
| service → errors, schemas, ไฟล์ PURE                 | ✓                                       |                                                       |
| service → repo                                       | **แค่ type hint** (ใต้ `TYPE_CHECKING`) |                                                       |
| service → fastapi / pymongo / bson                   | ✗                                       | กฎข้อ 1                                               |
| feature A service → feature B **service**            | ✓                                       | `projects/service` → `sites.service.analyze_and_save` |
| feature A → feature B **repo** ผ่าน router           | ✓                                       | `projects/router` ใช้ `get_site_repo` ของ sites       |
| feature A service → เขียน query collection ของ B เอง | ✗                                       | ต้องขอผ่าน repo ของ B                                 |
| repo → service                                       | ✗                                       | ทิศกลับ                                               |

---

## 10. เพิ่ม feature ใหม่ / เขียน test

### เพิ่ม feature (ตัวอย่าง: bookmarks)

1. `mkdir app/bookmarks`
2. `schemas.py` — request/response หน้าตาเป็นยังไง (เริ่มจากตรงนี้ = เริ่มจากสัญญากับ frontend)
3. `repo.py` — `class BookmarkRepo` มี method ที่ต้องใช้ (`add`, `list_by_user`, `delete`) ใช้ `oid()` / `out()` จาก `shared/mongo.py`
4. `service.py` — กฎ (เช่น ห้าม bookmark ซ้ำ → `raise AppError(...)`) รับ repo เป็น parameter, import repo ใต้ `TYPE_CHECKING`
5. `router.py` — `get_repo()` + endpoint ละบรรทัด, ต้อง login ใส่ `user: dict = Depends(get_current_user)` จาก `app.auth.router`
6. `main.py` — เพิ่มใน tuple ของ `include_router`
7. `tests/test_bookmarks_service.py` — FakeRepo + test กฎ

### เขียน test

```python
class FakeBookmarks:                       # มี method ชื่อเดียวกับ BookmarkRepo
    def __init__(self): self.rows = []
    def add(self, user_email, place_id): self.rows.append((user_email, place_id))
    def exists(self, user_email, place_id): return (user_email, place_id) in self.rows

def test_cannot_bookmark_twice():
    repo = FakeBookmarks()
    service.add_bookmark(repo, "a@x.com", "P1")
    with pytest.raises(AppError):
        service.add_bookmark(repo, "a@x.com", "P1")
```

test ผ่าน HTTP ทั้งเส้น (ยังไม่ต่อ DB):

```python
from fastapi.testclient import TestClient
app.dependency_overrides[get_repo] = lambda: FakeBookmarks()
TestClient(app).post("/api/bookmarks", json={...})
```

---

## 11. ย้ายอะไรมาจากไหน + สิ่งที่เปลี่ยน

### ตารางย้าย

| ของเดิม (pinup-backend)                                                    | ตอนนี้                                         |
| -------------------------------------------------------------------------- | ---------------------------------------------- |
| `routers/x.py`                                                             | `x/router.py`                                  |
| `schemas/x.py`                                                             | `x/schemas.py`                                 |
| `services/x_service.py` ส่วน `db.xxx...` + `ObjectId`                      | `x/repo.py`                                    |
| `services/x_service.py` ส่วนกฎ/ขั้นตอน                                     | `x/service.py`                                 |
| `services/sites_service.py` → `analyze_polygon_spatial` + helper           | `sites/analysis.py`                            |
| `services/geojson.py`                                                      | รวมเข้า `admin/repo.py` + `admin/service.py`   |
| `utils/zoning_mapping`, `bkk_main_zoning_rules`, `risk_evaluation`         | `sites/zoning_mapping`, `zoning_rules`, `risk` |
| `utils/auth.py` + JWT/Google ใน `auth_service.py`                          | `auth/security.py`                             |
| `utils/email.py`                                                           | `auth/email.py`                                |
| `utils/thai_tfdf.py`                                                       | `ai_chat/tfidf.py`                             |
| `utils/mock_search_data.py`                                                | `search/mock_data.py`                          |
| `utils/` geo ที่ใช้หลายที่                                                 | `shared/geo/`                                  |
| `data/` (transit json + loader)                                            | `transit/loader.py` + `transit/data/`          |
| `core/config.py`, `db/database.py`, `dependencies.py`                      | `config.py`, `db.py`                           |
| `utils/convert_coor`, `translate`, `distance_calculator`, `utils/__init__` | **ลบ** — ไม่มีใครเรียกใช้                      |

### แก้บั๊ก / ปรับปรุง

- **route ที่ใช้ pymongo เปลี่ยน `async def` → `def`**
  pymongo เป็น sync: ถ้าเรียกใน `async def` ระหว่างรอ DB **ทั้งแอปหยุดรับ request อื่น**
  `def` → FastAPI รันใน threadpool แยก → request อื่นไม่ต้องรอ
  (ยกเว้น 3 route ใน auth ที่ต้อง `await` ส่งเมล — มี `ponytail:` comment ไว้)
- **`POST /api/ai-chat/ask` คำถามว่าง:** เดิมได้ **500** เพราะ `except Exception` ใน router ดักโดน `HTTPException(400)` → ตอนนี้ได้ **400** ตามตั้งใจ
- **สร้าง site ใน project:** เดิม insert แล้ว update `project_id` อีกรอบ (2 write) → ตอนนี้ insert ครั้งเดียว
- **ลบ `try/except Exception → 500` ที่ครอบทุกฟังก์ชันใน admin / search** — FastAPI ตอบ 500 เองอยู่แล้ว
  ต่างแค่ข้อความ: เดิมส่ง `str(e)` ออกไป (อาจหลุดรายละเอียดภายในให้ผู้ใช้เห็น) ตอนนี้ได้ "Internal Server Error"

### ไม่ได้เปลี่ยน (ตั้งใจ — ย้ายโครงก่อน แก้ทีหลัง)

- `list_projects` นับ site แบบ N+1 (query 1 ครั้งต่อ project) — อยู่ที่ `SiteRepo.count_by_project` ที่เดียว แก้เป็น aggregate ได้โดยไม่แตะ service
- `ai_chat` — ดู [7.8](#78-ai_chat--แชตถามกฎผังเมือง-rag--typhoon-llm)
- places / transit เรียก Google ใน service ตรง — ดู [7.5](#75-places--รายละเอียดสถานที่จาก-google-places)
- docstring ยาว ๆ ของ route ถูกตัด (เหลือ `summary`) → คำอธิบายใน Swagger สั้นลง

---

## 12. ตรวจแล้วว่าเหมือนเดิม

- **route table:** 42 route ตรงกับ pinup-backend ทุกตัว (method + path)
- **parity test:** รันทั้ง 2 แอปบน mongomock (Mongo จำลองใน memory) ยิง request ชุดเดียวกัน 41 ครั้ง
  - projects, sites, admin, bdi, search, transit, places
  - auth ทั้ง flow: สมัคร → สมัครซ้ำ → login ก่อนยืนยัน → ส่งเมลซ้ำ → ยืนยัน → login ผิด/ถูก → me → แก้โปรไฟล์ → เปลี่ยนรหัส → ลืมรหัส → รีเซ็ต → ใช้ reset token แทน login
  - **status + body ตรงกันทั้งหมด** ต่างแค่ ObjectId ในข้อความ และเวลา `exp` ใน JWT
- **กฎข้อ 1:** ไม่มี `service.py` ไหน import fastapi / pymongo / bson
- **unit test:** `tests/` ผ่าน โดยไม่มี Mongo

**ยังไม่ได้ทดสอบ:** MongoDB จริง, Google Places / Typhoon / SMTP จริง

---

## 13. รัน

```bash
cd pinup-lite
cp ../../pinup-backend/.env .      # ใช้ env เดิม (.env อยู่ใน .gitignore แล้ว)
pip install -r requirements.txt
uvicorn app.main:app --reload       # หรือ make dev (docker)
python -m pytest tests              # ไม่ต้องมี .env / Mongo
```

env ที่ต้องมี: `MONGO_URI`, `DB_NAME`, `SECRET_KEY`, `GOOGLE_MAPS_API_KEY`, `TYPHOON_API_KEY`, `GOOGLE_CLIENT_ID`, `MAIL_*`, `FRONTEND_URL`
