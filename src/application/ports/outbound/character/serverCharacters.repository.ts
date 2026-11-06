/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → PORT (Outbound / Driven port)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: "ปลั๊กตัวเมีย" — interface ที่ use case ประกาศว่า
 *             "ฉันต้องการใครสักคนที่ทำสิ่งเหล่านี้ได้" โดยไม่สนว่าเป็น Mongo, Postgres,
 *             Redis, หรือ array ใน memory
 *
 * ข้างในมี:
 *   - ServerKey / CharacterParams / GameServer : type ของ input/output ของ port
 *   - ServerCharactersRepository                : สัญญา (contract) ที่ adapter ต้อง implement
 *
 * คนที่ใช้ port นี้   : use case (application/usecases/character/*)
 * คนที่ implement    : adapter/outbound/repositories/character/serverCharacters.repository.mongo.ts
 * คนที่ผูกสองฝั่งเข้าหากัน : application/application.providers.ts (ผ่าน DI token)
 *
 * กฎ:
 *   ✅ รับ/คืนเป็น Domain Model (ServerCharacters) เสมอ
 *   ❌ ห้ามคืน Mongoose Document / Entity / อะไรที่ผูกกับ DB
 *   ❌ ห้ามตั้งชื่อ method ตาม DB (เช่น `aggregate`, `findOneLean`) — ตั้งตามความต้องการของธุรกิจ
 *
 * สังเกต: Dependency Inversion — interface อยู่ฝั่ง application (คนใช้)
 *          ไม่ใช่ฝั่ง adapter (คนทำ) → ลูกศร dependency ชี้ "เข้าหา" แกนกลางเสมอ
 */
import { ServerCharacters } from '../../../../domain/model/serverCharacters.model';

export interface ServerKey {
    gagaId: string;
    gameCode: string;
    serverId: string;
}

export interface CharacterParams extends ServerKey {
    serverName: string;
    characterId: string;
    characterName: string;
}

export interface GameServer {
    serverId: string;
    serverName: string;
}

export interface ServerCharactersRepository {
    findByKey(key: ServerKey): Promise<ServerCharacters | undefined>;
    findByGagaId(gagaId: string, gameCode: string): Promise<ServerCharacters[]>;
    findServersByGameCode(gameCode: string): Promise<GameServer[]>;
    /** โยน error ถ้าซ้ำ */
    create(server: ServerCharacters): Promise<void>;
    updateByKeyId(key: ServerKey, server: ServerCharacters): Promise<void>;
}
