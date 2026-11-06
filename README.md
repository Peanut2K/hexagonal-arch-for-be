# Hexagonal Architecture — Study Skeleton (จาก gaga-core-be)

โฟลเดอร์นี้คือ **โครงกระดูก** ของ `gaga-core-be` (NestJS + MongoDB) ที่ตัดเหลือ **feature เดียว (character)
แบบครบทุก layer** เพื่อให้เห็นว่า request 1 ตัววิ่งผ่าน Hexagonal ยังไงตั้งแต่ HTTP จนถึง DB

- path ทุกไฟล์ **ตรงกับ repo จริง** → เปิดไฟล์คู่กันเทียบได้เลย
- ทุกไฟล์มี **comment ภาษาไทยด้านบน** บอกว่า: อยู่ layer ไหน / ข้างในมีอะไร / import อะไรได้-ไม่ได้
- โค้ดถูกตัดให้สั้นลง (ไม่มี Redis cache, logger, config) — **ไม่ได้ตั้งใจให้ run** แต่ให้อ่าน
- อยากเอาไปใช้กับ Python → อ่าน [FASTAPI.md](FASTAPI.md)

---

## 1. Hexagonal คืออะไร (ฉบับ 30 วินาที)

```
                 ┌────────────────────────────────────────────┐
   HTTP  ───▶    │  ADAPTER (inbound)                         │
   gRPC  ───▶    │  controller, dto, guard, response mapper   │
   Queue ───▶    └──────────────────┬─────────────────────────┘
                                    │ เรียก use case
                 ┌──────────────────▼─────────────────────────┐
                 │  APPLICATION                               │
                 │  usecase  ── ใช้ ──▶  port (interface)      │
                 │  command / result                          │
                 │        ┌──────────────────────┐            │
                 │        │  DOMAIN              │            │
                 │        │  model, errors       │            │
                 │        └──────────────────────┘            │
                 └──────────────────▲─────────────────────────┘
                                    │ implements port
                 ┌──────────────────┴─────────────────────────┐
   MongoDB ◀─    │  ADAPTER (outbound)                        │
   Redis   ◀─    │  repository.mongo, mapper, schema, entity  │
   Funtap  ◀─    │  gateway.http, emailSender.smtp            │
                 └────────────────────────────────────────────┘
```

**กฎข้อเดียวที่ต้องจำ — Dependency Rule:**
> ลูกศร `import` ชี้ **เข้าหาตรงกลาง** เสมอ
> `adapter → application → domain` ✅
> `domain → application` ❌ `application/usecases → adapter` ❌

- **Port** = interface ที่ "ข้างใน" ประกาศว่าต้องการอะไรจากโลกภายนอก (`ServerCharactersRepository`)
- **Adapter** = ของจริงที่ทำตาม port (`ServerCharactersRepositoryMongo`)
- **Composition root** = ที่เดียวที่บอกว่า port ไหนใช้ adapter ไหน (`application.providers.ts`)

ผลลัพธ์: เปลี่ยน DB / เพิ่ม cache / test use case ด้วย fake → **ไม่ต้องแตะ business logic**

---

## 2. Tree Structure + หน้าที่ของแต่ละไฟล์

```
hexagonal-skeleton/
├── README.md                        ← ไฟล์นี้
├── FASTAPI.md                       ← วิธีเอาไปใช้กับ FastAPI
└── src/
    ├── main.ts                      ← entry point: สร้าง app, ValidationPipe, listen port
    ├── app.module.ts                ← root module: import AdapterModule + global exception filter
    │
    ├── domain/                      ━━━ ชั้นในสุด: ไม่รู้จัก framework/DB/HTTP เลย ━━━
    │   ├── model/
    │   │   └── serverCharacters.model.ts      ← รูปร่างข้อมูลธุรกิจ (ไม่มี _id, keyId)
    │   └── errors/
    │       └── errorCodes.ts                  ← ErrorCode enum + AppException (ไม่มี HTTP status)
    │
    ├── application/                 ━━━ business flow: "ระบบทำอะไรได้บ้าง" ━━━
    │   ├── application.module.ts              ← Nest module: ลงทะเบียน use case + port→adapter
    │   ├── application.usecases.ts            ← array ของ use case ทุกตัว
    │   ├── application.providers.ts           ← ★ COMPOSITION ROOT: { provide: PORT_TOKEN, useClass: Adapter }
    │   ├── commands/
    │   │   └── character/
    │   │       └── submitServerCharacterCommand.ts   ← input ของ use case (plain object, camelCase)
    │   ├── results/                           ← (ว่างใน skeleton) output ของ use case ถ้าไม่อยากคืน domain ตรง ๆ
    │   ├── ports/
    │   │   └── outbound/
    │   │       └── character/
    │   │           └── serverCharacters.repository.ts ← ★ PORT: interface ที่ use case ต้องการ
    │   └── usecases/
    │       └── character/
    │           ├── submitServerCharacter.usecase.ts      ← ★ USE CASE: 1 class = 1 action, method `handler()`
    │           └── submitServerCharacter.usecase.spec.ts ← unit test ด้วย fake repo (ไม่มี DB)
    │
    ├── adapter/                     ━━━ ทุกอย่างที่แตะโลกภายนอก ━━━
    │   ├── adapter.module.ts                  ← Nest module: controllers, Mongo connection, interceptor
    │   ├── inbound/                           ── ขาเข้า (driving): โลกภายนอก → เรียกเรา
    │   │   ├── controllers/
    │   │   │   └── identity.controller.ts     ← รับ HTTP → DTO→Command → use case → Domain→JSON
    │   │   ├── dtos/
    │   │   │   └── identityVerification/
    │   │   │       └── vnCharacter.dto.ts     ← รูปร่าง request body + class-validator
    │   │   ├── mappers/
    │   │   │   └── identityVerification/
    │   │   │       └── vnCharacter.response.ts ← Domain → JSON response (snake_case)
    │   │   ├── guards/
    │   │   │   └── jwtAuth.guard.ts           ← ตรวจ Bearer JWT แปะ req.user
    │   │   └── decorators/
    │   │       └── currentUser.decorator.ts   ← @CurrentUser() ดึง req.user
    │   └── outbound/                          ── ขาออก (driven): เราเรียกโลกภายนอก
    │       ├── database/
    │       │   └── mongoCollections.ts        ← ชื่อ collection ทั้งหมด
    │       ├── mappers/
    │       │   └── character/
    │       │       └── serverCharacters.mapper.ts  ← Entity ⇄ Domain (เติม/ทิ้ง keyId)
    │       └── repositories/
    │           ├── index.ts                   ← modelDefinitions ให้ MongooseModule.forFeature
    │           └── character/
    │               ├── serverCharacters.repository.mongo.ts ← ★ ADAPTER: implements port ด้วย Mongoose
    │               ├── entities/
    │               │   └── serverCharacters.entity.ts       ← type ของ document จาก DB (มี _id, keyId)
    │               └── schemas/
    │                   └── serverCharacters.schema.ts       ← Mongoose @Schema + index
    │
    └── common/                      ━━━ ของใช้ร่วม (cross-cutting) ━━━
        ├── tokens/
        │   └── index.ts                       ← DI token string แทน interface (TS interface หายตอน runtime)
        ├── exceptions/
        │   └── errorCodes.ts                  ← ตาราง ErrorCode → HTTP status / message
        └── http/
            ├── allExceptions.filter.ts        ← ดัก AppException → HTTP response มาตรฐาน
            └── responseEnvelope.interceptor.ts ← ห่อ response สำเร็จเป็น { code, message, data, trace_id }
```

### ใครอยู่ใน repo จริงแต่ไม่อยู่ใน skeleton

| ใน repo จริง | คืออะไร | ทำไมตัดออก |
|---|---|---|
| `adapter/outbound/gateways/funtap/` + `ports/outbound/funtap/` | เรียก API ภายนอก — **เป็น port/adapter เหมือน repository ทุกประการ** | pattern เดียวกัน |
| `adapter/outbound/notification/emailSender.{console,smtp}.ts` | 2 adapter ของ port เดียว เลือกด้วย config | ดูตัวอย่างใน comment ของ `application.providers.ts` |
| `adapter/outbound/repositories/redisCache/` | cache ที่ adapter ใช้ภายใน | use case ไม่รู้ว่ามี — ดู comment ใน repository.mongo.ts |
| `adapter/outbound/repositories/transactions/` | port สำหรับ Mongo transaction | หัวข้อขั้นสูง ดูข้อ 5 |
| `adapter/inbound/web/` | หน้า HTML (Handlebars) — **เป็น inbound adapter อีกตัว** เรียก use case ชุดเดียวกับ REST | ใหญ่เกิน |
| `adapter/inbound/middleware/`, `validators/` | CORS, security header, custom validator | เรื่อง HTTP ล้วน |
| `application/bootstrap/` | seed ข้อมูลตอน start | ไม่เกี่ยวกับ pattern |
| `configs/` | อ่าน env | ไม่เกี่ยวกับ pattern |

---

## 3. เดิน 1 request ตั้งแต่ต้นจนจบ

`POST /identity/vn/character` + `Authorization: Bearer <jwt>` + body `{ server_id, server_name, character_id, character_name }`

| # | ไฟล์ | เกิดอะไรขึ้น | ข้อมูลอยู่ในรูป |
|---|---|---|---|
| 1 | `main.ts` → `ValidationPipe` | validate body ตาม decorator ใน DTO, ผิด → 400 | JSON |
| 2 | `jwtAuth.guard.ts` | verify JWT → `req.user = payload` | JWT payload |
| 3 | `identity.controller.ts` | `playerOf(user)` + `characterOf(player, dto)` | **DTO → Command** |
| 4 | `submitServerCharacter.usecase.ts` | `repo.findByKey(command)` ผ่าน **port** | Command |
| 5 | (DI) `application.providers.ts` | token → `ServerCharactersRepositoryMongo` | — |
| 6 | `serverCharacters.repository.mongo.ts` | `model.findOne({ keyId })` | Entity |
| 7 | `serverCharacters.mapper.ts` | `toDomain(entity)` ทิ้ง `keyId`, `_id` | **Entity → Domain** |
| 8 | use case | ไม่มี draft → `throw AppException(INVALID_REQUEST)` / มี → เปลี่ยนเป็น `submitted` | Domain |
| 9 | repository + mapper | `toEntity(domain)` → `updateOne` | **Domain → Entity** |
| 10 | controller | `VnCharacterResponse.toResponse(domain)` | **Domain → JSON** |
| 11 | `responseEnvelope.interceptor.ts` | ห่อ `{ code: 'OK', data, ... }` | JSON |
| 11' | `allExceptions.filter.ts` (ถ้า error) | `ERROR_STATUS_MAP[INVALID_REQUEST]` → 400 | JSON |

**สังเกตจำนวนครั้งที่ข้อมูลเปลี่ยนรูป:** JSON → DTO → Command → Entity → Domain → Entity → JSON
แต่ละรอยต่อมี **ไฟล์ mapper/แปลง ของมันเอง** — นี่แหละคือ "ราคา" ของ Hexagonal (ไฟล์เยอะ)
แลกกับ: แต่ละชั้นเปลี่ยนได้อิสระ

---

## 4. ตาราง "ใคร import ใครได้"

| ไฟล์ใน ↓ import จาก → | domain | application (ports/commands/usecases) | adapter | framework (Nest/Mongoose/Express) |
|---|:-:|:-:|:-:|:-:|
| **domain/** | ✅ | ❌ | ❌ | ❌ |
| **application/usecases, ports, commands, results** | ✅ | ✅ | ❌ | ⚠ เฉพาะ `@Injectable/@Inject` (trade-off ของ repo นี้) |
| **application/application.providers.ts** (wiring) | ✅ | ✅ | ✅ | ✅ |
| **adapter/** | ✅ | ✅ | ✅ | ✅ |
| **common/** | ✅ | ❌ (ยกเว้น tokens) | ❌ | ✅ |

เช็คง่าย ๆ ด้วยคำสั่ง (ใน repo จริง):
```bash
grep -rn "from '.*adapter" src/application/usecases   # ต้องว่าง
grep -rn "mongoose\|express" src/domain src/application/usecases   # ต้องว่าง
```

---

## 5. จุดที่ควรรู้ (repo นี้ "ไม่ textbook" ตรงไหน และทำไม)

1. **ไม่มี `ports/inbound/`** — controller inject use case class ตรง ๆ
   Textbook บอกให้มี interface `SubmitServerCharacterPort` ครอบ use case อีกชั้น แต่ถ้ามี implementation เดียว
   interface นั้นไม่ได้ให้อะไรเพิ่ม → ข้ามได้ (เพิ่มทีหลังเมื่อมี implementation ที่ 2 จริง)

2. **Domain เป็น anemic model** — `ServerCharacters` มีแต่ field, rule อยู่ใน use case
   ใช้ได้ดีเมื่อ rule ง่าย ถ้า rule เริ่มซ้ำกันหลาย use case ให้ย้ายเข้า domain:
   ```ts
   // domain/model/serverCharacters.model.ts
   markSubmitted(characterId: string, name: string, now: Date): void {
       const c = this.characters.find(x => x.characterId === characterId);
       if (!c) throw new AppException(ErrorCode.INVALID_REQUEST, 'No draft');
       Object.assign(c, { characterName: name, status: 'submitted', submittedAt: now, updatedAt: now });
   }
   ```

3. **Use case ใช้ `@Injectable()` ของ Nest** — framework รั่วเข้ามานิดหน่อยเพื่อแลกกับ DI อัตโนมัติ
   logic ไม่พึ่ง Nest จึงยัง `new UseCase(fake)` ใน test ได้

4. **Composition root อยู่ในโฟลเดอร์ `application/`** (`application.providers.ts`)
   ไฟล์นี้ import adapter — เป็นข้อยกเว้นที่ตั้งใจ เพราะมันคือ wiring ไม่ใช่ logic
   (หลายโปรเจกต์ย้ายไปไว้ `src/bootstrap/` หรือ `main.ts` เพื่อให้กฎ import สะอาด 100%)

5. **Transaction** — repo จริงมี `TransactionRepository` port ที่คืน `ITransaction { session: ClientSession }`
   ซึ่งยังมี type ของ mongoose หลุดเข้า application อยู่ = รอยรั่วที่ยอมรับเพื่อความง่าย
   แบบ textbook คือ Unit of Work port ที่ไม่เปิดเผย type ของ DB

6. **Error 2 ชั้น** — domain รู้แค่ `ErrorCode`, การแปลงเป็น HTTP อยู่ใน `common/` + filter
   → use case เดียวกันเรียกจาก REST/HTML page/queue ได้ แต่ละที่แปลง error เอง

---

## 6. Checklist เพิ่ม feature ใหม่ (เช่น "ลบตัวละคร")

1. `domain/model/` — ต้องเพิ่ม field/type ไหม?
2. `application/ports/outbound/<feature>/` — port ต้องมี method ใหม่ไหม? (`deleteByKey`)
3. `application/commands/<feature>/` — สร้าง `DeleteServerCharacterCommand`
4. `application/usecases/<feature>/` — สร้าง `DeleteServerCharacter.usecase.ts` + `.spec.ts` (test ด้วย fake)
5. `application/application.usecases.ts` — เพิ่ม use case เข้า array
6. `adapter/outbound/repositories/<feature>/` — implement method ใหม่ใน `.mongo.ts`
7. `adapter/inbound/dtos/` + `mappers/` — DTO และ response mapper
8. `adapter/inbound/controllers/` — route ใหม่ (4 ขั้น: รับ → แปลง → เรียก → แปลงกลับ)
9. port ใหม่ทั้งตัว? → เพิ่ม token ใน `common/tokens` + 1 บรรทัดใน `application.providers.ts`

ลำดับนี้ **ไล่จากในออกนอก** — เขียน + test use case ได้ก่อนจะมี DB หรือ controller ด้วยซ้ำ
