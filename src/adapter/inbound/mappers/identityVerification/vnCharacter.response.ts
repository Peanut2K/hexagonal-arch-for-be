/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → INBOUND → RESPONSE MAPPER
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: แปลง Domain Model → JSON ที่จะส่งกลับ client
 *
 * ทำไมไม่ return domain model ตรง ๆ?
 *   1. API contract เป็น snake_case, โค้ดภายในเป็น camelCase
 *   2. เลือกได้ว่าจะ "ไม่ส่ง" field ไหน (เช่น createdAt, gagaId) — ป้องกันข้อมูลรั่ว
 *   3. เปลี่ยน domain ภายในได้โดยไม่ทำ API ของ client พัง
 *
 * ทิศทางการแปลงทั้งหมดใน 1 request:
 *   JSON ──(DTO)──▶ Command ──▶ UseCase ──▶ Domain ──(ไฟล์นี้)──▶ JSON
 */
import { ServerCharacters } from '../../../../domain/model/serverCharacters.model';

export class VnCharacterResponse {
    static toResponse(r: ServerCharacters) {
        return {
            server_id: r.serverId,
            server_name: r.serverName,
            characters: r.characters.map((c) => ({
                character_id: c.characterId,
                character_name: c.characterName,
                status: c.status,
            })),
        };
    }
}
