/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → PERSISTENCE MAPPER
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ตัวแปลง 2 ทาง ระหว่าง Entity (DB) ⇄ Domain Model
 *
 * ข้างในมี:
 *   - keyId()      : สร้างคีย์ที่ใช้เฉพาะใน DB (domain ไม่เคยเห็นค่านี้)
 *   - toDomain()   : Entity → Domain  (ทิ้ง _id, keyId)
 *   - toEntity()   : Domain → Entity  (เติม keyId)
 *
 * ใครเรียก: repository adapter เท่านั้น (serverCharacters.repository.mongo.ts)
 *
 * ทำไมต้องมี? ทำไมไม่ใช้ Mongoose document เป็น domain เลย?
 *   ถ้าใช้ document ตรง ๆ → use case ได้ object ที่มี .save(), ._id, getter แปลก ๆ
 *   → วันที่เปลี่ยน DB ต้องไล่แก้ทุก use case
 *   mapper ทำให้ "รอยต่อ" อยู่ที่เดียว
 *
 * (repo จริงใช้ lib `builder-pattern` — skeleton นี้เขียน object literal ตรง ๆ ให้อ่านง่าย)
 */
import { ServerKey } from '../../../../application/ports/outbound/character/serverCharacters.repository';
import { PlayerCharacter, ServerCharacters } from '../../../../domain/model/serverCharacters.model';
import {
    PlayerCharacterEntity,
    ServerCharactersEntity,
} from '../../repositories/character/entities/serverCharacters.entity';

export class ServerCharactersMapper {
    /** คีย์สำหรับ DB เท่านั้น — 1 record ต่อ gagaId + game + server */
    static keyId(key: ServerKey): string {
        return `${key.gagaId}_${key.gameCode}_${key.serverId}`;
    }

    static characterToDomain(e: PlayerCharacterEntity): PlayerCharacter {
        return {
            characterId: e.characterId,
            characterName: e.characterName,
            status: e.status,
            createdAt: e.createdAt,
            updatedAt: e.updatedAt,
            submittedAt: e.submittedAt,
        };
    }

    static toDomain(e: ServerCharactersEntity): ServerCharacters {
        return Object.assign(new ServerCharacters(), {
            gagaId: e.gagaId,
            gameCode: e.gameCode,
            serverId: e.serverId,
            serverName: e.serverName,
            characters: e.characters.map(ServerCharactersMapper.characterToDomain),
            createdAt: e.createdAt,
            updatedAt: e.updatedAt,
        });
    }

    static toEntity(d: ServerCharacters): ServerCharactersEntity {
        return {
            keyId: ServerCharactersMapper.keyId(d),
            gagaId: d.gagaId,
            gameCode: d.gameCode,
            serverId: d.serverId,
            serverName: d.serverName,
            characters: d.characters.map((c) => ({ ...c })),
            createdAt: d.createdAt,
            updatedAt: d.updatedAt,
        };
    }
}
