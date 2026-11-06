# เอา Hexagonal จาก gaga-core-be ไปใช้กับ FastAPI

แนวคิดเหมือนเดิม 100% ต่างกันแค่ "เครื่องมือ" ของแต่ละ layer

## 1. ตารางเทียบ NestJS ↔ FastAPI

| แนวคิด | gaga-core-be (NestJS) | FastAPI |
|---|---|---|
| Domain model | `class ServerCharacters` | `@dataclass` (**ไม่ใช่** Pydantic, **ไม่ใช่** SQLAlchemy model) |
| Port | `interface ServerCharactersRepository` | `typing.Protocol` (หรือ `abc.ABC`) |
| DI token | `SERVER_CHARACTERS_REPOSITORY_PORT` string | **ไม่ต้องมี** — Protocol/class ยังอยู่ตอน runtime |
| Use case | `@Injectable() class ...UseCase { handler() }` | class ธรรมดา ไม่มี decorator เลย |
| Command | `interface ...Command` | `@dataclass(frozen=True)` |
| Composition root | `application.providers.ts` (`provide/useClass`) | `bootstrap/container.py` — ฟังก์ชันที่ใช้กับ `Depends()` |
| Controller | `@Controller` + `@Post` | `APIRouter` + `@router.post` |
| DTO + validation | class-validator + `ValidationPipe` | Pydantic `BaseModel` (validate อัตโนมัติ) |
| Response mapper | `VnCharacterResponse.toResponse()` | Pydantic response model + ฟังก์ชัน `from_domain()` |
| Guard + `@CurrentUser` | `JwtAuthGuard` + param decorator | `Depends(get_current_user)` |
| Exception filter | `AllExceptionsFilter` | `@app.exception_handler(AppException)` |
| Envelope interceptor | `ResponseEnvelopeInterceptor` | ห่อใน response model หรือ middleware |
| Mongoose schema / entity | `schemas/` + `entities/` | SQLAlchemy model / Beanie Document / dict ของ Motor |
| Persistence mapper | `ServerCharactersMapper` | ฟังก์ชัน `to_domain()` / `to_row()` ในไฟล์ adapter |
| Unit test | jest + fake object | pytest + fake class |

## 2. Tree Structure ที่แนะนำ

```
app/
├── main.py                              ← สร้าง FastAPI(), include router, exception handler, lifespan
├── domain/
│   ├── models.py                        ← @dataclass ServerCharacters, PlayerCharacter
│   └── errors.py                        ← ErrorCode(Enum), AppException
├── application/
│   ├── ports/
│   │   └── server_characters_repository.py   ← class ServerCharactersRepository(Protocol)
│   ├── commands.py                      ← @dataclass SubmitServerCharacterCommand
│   └── usecases/
│       └── submit_server_character.py   ← class SubmitServerCharacterUseCase
├── adapters/
│   ├── inbound/
│   │   └── http/
│   │       ├── routers/identity.py      ← APIRouter
│   │       ├── schemas.py               ← Pydantic request/response (= DTO + response mapper)
│   │       ├── auth.py                  ← get_current_user (= JwtAuthGuard + @CurrentUser)
│   │       └── errors.py                ← exception handler (= AllExceptionsFilter + ERROR_STATUS_MAP)
│   └── outbound/
│       └── persistence/
│           ├── mongo_server_characters.py    ← implements port ด้วย Motor
│           └── memory_server_characters.py   ← (optional) สำหรับ dev/test
├── bootstrap/
│   └── container.py                     ← ★ composition root: port → adapter
└── tests/
    └── test_submit_server_character.py
```

> ตั้งชื่อเป็น "layer ก่อน feature" แบบ repo นี้ หรือ "feature ก่อน layer" (`app/character/{domain,application,adapters}`) ก็ได้
> โปรเจกต์เล็ก → layer ก่อน, โปรเจกต์ใหญ่หลายทีม → feature ก่อน

## 3. โค้ดทีละ layer (feature เดียวกับใน skeleton)

### domain/models.py
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

CharacterFormStatus = Literal["pending", "submitted"]

@dataclass
class PlayerCharacter:
    character_id: str
    character_name: str
    status: CharacterFormStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None

@dataclass
class ServerCharacters:
    gaga_id: str
    game_code: str
    server_id: str
    server_name: str
    characters: list[PlayerCharacter] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### domain/errors.py
```python
from enum import Enum

class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    SERVER_ERROR = "SERVER_ERROR"

class AppException(Exception):
    def __init__(self, code: ErrorCode, message: str | None = None):
        super().__init__(message or code.value)
        self.code = code
        self.message = message
```

### application/ports/server_characters_repository.py
```python
from typing import Protocol
from app.domain.models import ServerCharacters

class ServerCharactersRepository(Protocol):
    async def find_by_key(self, gaga_id: str, game_code: str, server_id: str) -> ServerCharacters | None: ...
    async def update(self, server: ServerCharacters) -> None: ...
```
> `Protocol` = structural typing: adapter ไม่ต้อง inherit ก็ได้ ขอแค่ method ตรง (mypy/pyright เช็คให้)
> อยากให้บังคับตอน runtime → ใช้ `abc.ABC` + `@abstractmethod` แทน

### application/commands.py
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SubmitServerCharacterCommand:
    gaga_id: str
    game_code: str
    server_id: str
    server_name: str
    character_id: str
    character_name: str
```

### application/usecases/submit_server_character.py
```python
from datetime import datetime, timezone
from app.application.commands import SubmitServerCharacterCommand
from app.application.ports.server_characters_repository import ServerCharactersRepository
from app.domain.errors import AppException, ErrorCode
from app.domain.models import ServerCharacters

class SubmitServerCharacterUseCase:
    # ไม่มี import fastapi / motor / pydantic เลย ← นี่คือเป้าหมาย
    def __init__(self, repo: ServerCharactersRepository):
        self.repo = repo

    async def handle(self, cmd: SubmitServerCharacterCommand) -> ServerCharacters:
        server = await self.repo.find_by_key(cmd.gaga_id, cmd.game_code, cmd.server_id)
        draft = next((c for c in server.characters if c.character_id == cmd.character_id), None) if server else None
        if not server or not draft:
            raise AppException(ErrorCode.INVALID_REQUEST, "No identity form was sent for this character.")

        now = datetime.now(timezone.utc)
        draft.character_name = cmd.character_name
        draft.status = "submitted"
        draft.submitted_at = draft.updated_at = now
        server.server_name = cmd.server_name
        server.updated_at = now
        await self.repo.update(server)
        return server
```

### adapters/outbound/persistence/mongo_server_characters.py
```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.domain.models import PlayerCharacter, ServerCharacters

def _key_id(gaga_id: str, game_code: str, server_id: str) -> str:
    return f"{gaga_id}_{game_code}_{server_id}"   # รายละเอียด DB — domain ไม่เคยเห็น

def _to_domain(doc: dict) -> ServerCharacters:      # = ServerCharactersMapper.toDomain
    return ServerCharacters(
        gaga_id=doc["gagaId"], game_code=doc["gameCode"], server_id=doc["serverId"],
        server_name=doc["serverName"],
        characters=[PlayerCharacter(
            character_id=c["characterId"], character_name=c["characterName"], status=c["status"],
            created_at=c["createdAt"], updated_at=c["updatedAt"], submitted_at=c.get("submittedAt"),
        ) for c in doc["characters"]],
        created_at=doc["createdAt"], updated_at=doc["updatedAt"],
    )

def _to_doc(s: ServerCharacters) -> dict:           # = ServerCharactersMapper.toEntity
    return {
        "keyId": _key_id(s.gaga_id, s.game_code, s.server_id),
        "gagaId": s.gaga_id, "gameCode": s.game_code, "serverId": s.server_id, "serverName": s.server_name,
        "characters": [{
            "characterId": c.character_id, "characterName": c.character_name, "status": c.status,
            "createdAt": c.created_at, "updatedAt": c.updated_at, "submittedAt": c.submitted_at,
        } for c in s.characters],
        "createdAt": s.created_at, "updatedAt": s.updated_at,
    }

class MongoServerCharactersRepository:              # ไม่ต้อง inherit Protocol ก็ได้
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["server_characters"]

    async def find_by_key(self, gaga_id, game_code, server_id):
        doc = await self.col.find_one({"keyId": _key_id(gaga_id, game_code, server_id)})
        return _to_domain(doc) if doc else None

    async def update(self, server):
        doc = _to_doc(server)
        await self.col.update_one({"keyId": doc["keyId"]}, {"$set": doc})
```
> ใช้ Postgres → เปลี่ยนไฟล์นี้เป็น SQLAlchemy model + session; ที่เหลือไม่ต้องแก้

### adapters/inbound/http/schemas.py  (= DTO + response mapper)
```python
from pydantic import BaseModel, Field
from app.domain.models import ServerCharacters

class VnCharacterRequest(BaseModel):            # = VnCharacterDto
    server_id: str = Field(min_length=1, max_length=64)
    server_name: str = Field(min_length=1, max_length=64)
    character_id: str = Field(min_length=1, max_length=64)
    character_name: str = Field(min_length=1, max_length=64)

class CharacterOut(BaseModel):
    character_id: str
    character_name: str
    status: str

class VnCharacterResponse(BaseModel):           # = VnCharacterResponse.toResponse
    server_id: str
    server_name: str
    characters: list[CharacterOut]

    @classmethod
    def from_domain(cls, s: ServerCharacters) -> "VnCharacterResponse":
        return cls(
            server_id=s.server_id, server_name=s.server_name,
            characters=[CharacterOut(character_id=c.character_id, character_name=c.character_name, status=c.status)
                        for c in s.characters],
        )
```

### adapters/inbound/http/auth.py  (= JwtAuthGuard + @CurrentUser)
```python
import jwt                                        # PyJWT
from fastapi import Header
from pydantic import BaseModel
from app.domain.errors import AppException, ErrorCode

class AccessTokenPayload(BaseModel):
    sub: str
    client_id: str | None = None
    token_use: str | None = None

def get_current_user(authorization: str = Header(default="")) -> AccessTokenPayload:
    if not authorization.startswith("Bearer "):
        raise AppException(ErrorCode.AUTH_INVALID_TOKEN)
    try:
        return AccessTokenPayload(**jwt.decode(authorization[7:], SECRET, algorithms=["HS256"]))
    except jwt.PyJWTError:
        raise AppException(ErrorCode.AUTH_INVALID_TOKEN)
```

### bootstrap/container.py  (★ composition root = application.providers.ts)
```python
from fastapi import Request
from app.adapters.outbound.persistence.mongo_server_characters import MongoServerCharactersRepository
from app.application.ports.server_characters_repository import ServerCharactersRepository
from app.application.usecases.submit_server_character import SubmitServerCharacterUseCase

# ที่เดียวที่รู้ว่า port ไหน = adapter ไหน
def get_server_characters_repo(request: Request) -> ServerCharactersRepository:
    return MongoServerCharactersRepository(request.app.state.db)

def get_submit_server_character(request: Request) -> SubmitServerCharacterUseCase:
    return SubmitServerCharacterUseCase(get_server_characters_repo(request))
```

### adapters/inbound/http/routers/identity.py  (= IdentityController)
```python
from fastapi import APIRouter, Depends
from app.adapters.inbound.http.auth import AccessTokenPayload, get_current_user
from app.adapters.inbound.http.schemas import VnCharacterRequest, VnCharacterResponse
from app.application.commands import SubmitServerCharacterCommand
from app.application.usecases.submit_server_character import SubmitServerCharacterUseCase
from app.bootstrap.container import get_submit_server_character
from app.domain.errors import AppException, ErrorCode

router = APIRouter(prefix="/identity")

@router.post("/vn/character", response_model=VnCharacterResponse)
async def vn_character(
    body: VnCharacterRequest,                                         # 1. รับ (validate แล้ว)
    user: AccessTokenPayload = Depends(get_current_user),
    usecase: SubmitServerCharacterUseCase = Depends(get_submit_server_character),
):
    if user.token_use == "client" or not user.client_id:
        raise AppException(ErrorCode.AUTH_FORBIDDEN)
    cmd = SubmitServerCharacterCommand(                               # 2. แปลง DTO → Command
        gaga_id=user.sub, game_code=user.client_id,
        server_id=body.server_id, server_name=body.server_name,
        character_id=body.character_id, character_name=body.character_name,
    )
    result = await usecase.handle(cmd)                                # 3. เรียก
    return VnCharacterResponse.from_domain(result)                    # 4. แปลงกลับ
```

### adapters/inbound/http/errors.py + main.py  (= AllExceptionsFilter + app.module)
```python
# errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.errors import AppException, ErrorCode

ERROR_STATUS = {
    ErrorCode.INVALID_REQUEST: 400, ErrorCode.AUTH_INVALID_TOKEN: 401,
    ErrorCode.AUTH_FORBIDDEN: 403, ErrorCode.SERVER_ERROR: 500,
}

async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=ERROR_STATUS[exc.code],
                        content={"code": exc.code.value, "message": exc.message or exc.code.value})

# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

@asynccontextmanager
async def lifespan(app: FastAPI):               # = MongooseModule.forRootAsync
    client = AsyncIOMotorClient(MONGODB_URI)
    app.state.db = client[DB_NAME]
    yield
    client.close()

app = FastAPI(lifespan=lifespan)
app.include_router(identity.router)
app.add_exception_handler(AppException, app_exception_handler)
```

### tests/test_submit_server_character.py
```python
import asyncio, pytest
from datetime import datetime
from app.application.commands import SubmitServerCharacterCommand
from app.application.usecases.submit_server_character import SubmitServerCharacterUseCase
from app.domain.errors import AppException, ErrorCode
from app.domain.models import PlayerCharacter, ServerCharacters

class FakeRepo:                                   # ไม่มี Mongo, ไม่มี FastAPI
    def __init__(self, server): self.server, self.saved = server, None
    async def find_by_key(self, *_): return self.server
    async def update(self, server): self.saved = server

CMD = SubmitServerCharacterCommand("VNGG0", "excalibur", "2", "S2", "1002", "DDH33")

def test_submits_draft():
    t = datetime(2026, 1, 1)
    repo = FakeRepo(ServerCharacters("VNGG0", "excalibur", "2", "old",
                    [PlayerCharacter("1002", "old", "pending", t, t)]))
    result = asyncio.run(SubmitServerCharacterUseCase(repo).handle(CMD))
    assert result.characters[0].status == "submitted"
    assert repo.saved is result

def test_rejects_without_draft():
    with pytest.raises(AppException) as e:
        asyncio.run(SubmitServerCharacterUseCase(FakeRepo(None)).handle(CMD))
    assert e.value.code is ErrorCode.INVALID_REQUEST
```

ทดสอบ route ทั้งเส้นโดยไม่ต่อ DB → override แค่ composition root:
```python
app.dependency_overrides[get_server_characters_repo] = lambda: FakeRepo(...)
```
(`get_submit_server_character` ต้องรับ repo ผ่าน `Depends(get_server_characters_repo)` แทนการเรียกตรง ๆ ถึงจะ override ได้)

## 4. คำแนะนำ / กับดักที่เจอบ่อยใน FastAPI

1. **อย่าใช้ Pydantic model เป็น domain** — สะดวกแต่ domain จะผูกกับ Pydantic version + validation ของ HTTP
   ใช้ `@dataclass` ใน domain, Pydantic เฉพาะใน `adapters/inbound/http/schemas.py`
   (ทีมเล็กที่ยอมรับ trade-off ใช้ Pydantic ใน domain ได้ แต่ให้ตัดสินใจโดยรู้ตัว)

2. **อย่าใช้ SQLAlchemy model เป็น domain** — เหตุผลเดียวกับที่ repo นี้แยก `schemas/` + `entities/` ออกจาก `domain/model/`
   lazy-load, session-bound object จะหลุดเข้า use case แล้วพังตอนนอก session

3. **`Depends()` = DI container ของคุณแล้ว** — ไม่ต้องลง `dependency-injector` หรือ lib อื่น จนกว่า container.py จะยาวจนอ่านไม่ไหว

4. **Use case ห้าม import `fastapi`** — ห้าม `raise HTTPException` ใน use case ให้ raise `AppException` แล้วให้ exception handler แปลง
   (เหมือน `AppException` + `AllExceptionsFilter` ใน repo นี้)

5. **Validate 2 ชั้น** — Pydantic เช็ค "รูปแบบ" (type, length), use case เช็ค "ธุรกิจ" (มี draft ไหม)

6. **async ให้ตลอดเส้น** — port เป็น `async def` → adapter ต้องใช้ driver async (Motor, asyncpg, SQLAlchemy async)
   ถ้าใช้ driver sync ใน `async def` จะ block event loop ทั้งตัว

7. **Transaction** — ทำ Unit of Work port (`async with uow: ...`) แทนการส่ง `session` ของ DB เข้า use case
   (repo นี้ส่ง Mongo `ClientSession` ผ่าน port = รอยรั่วที่ไม่ควรเลียนแบบ)

8. **อย่าสร้างทุกชั้นตั้งแต่วันแรก** — เริ่มจาก `domain` + `usecase` + `port` + adapter 1 ตัว
   ไม่ต้องมี inbound port, ไม่ต้องมี result class, ไม่ต้องมี generic `BaseRepository[T]`
   เพิ่มเมื่อมีเหตุผลจริง (มี implementation ที่ 2, มี consumer ที่ 2)

9. **CRUD ล้วน ๆ ไม่ต้อง Hexagonal** — endpoint ที่แค่อ่าน/เขียน DB ไม่มี rule
   ให้ router เรียก repository ตรง ๆ ก็พอ ใช้ Hexagonal กับส่วนที่มี business logic จริง
