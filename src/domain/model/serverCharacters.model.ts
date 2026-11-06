/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: DOMAIN (ชั้นในสุด — "หัวใจ" ของระบบ)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: Domain Model — รูปร่างของข้อมูลทางธุรกิจ "ตามที่ธุรกิจเข้าใจ"
 *             ไม่ใช่ตามที่ database เก็บ และไม่ใช่ตามที่ API รับ/ส่ง
 *
 * ข้างในมี:
 *   - CharacterFormStatus : ค่าสถานะที่ธุรกิจรู้จัก ('pending' | 'submitted')
 *   - PlayerCharacter     : ตัวละคร 1 ตัว
 *   - ServerCharacters    : ตัวละครทั้งหมดของ 1 คน บน 1 server ของ 1 เกม
 *
 * กฎเหล็ก:
 *   ✅ import ได้เฉพาะไฟล์ใน domain/ ด้วยกันเอง
 *   ❌ ห้าม import @nestjs/*, mongoose, express, class-validator ฯลฯ
 *   ❌ ห้ามมี `_id`, `keyId`, decorator ของ DB — นั่นเป็นเรื่องของ adapter
 *
 * สังเกต: ไม่มี `keyId` (คีย์ที่ Mongo ใช้ค้นหา) อยู่ในนี้
 *          → Mapper ฝั่ง outbound เป็นคนสร้าง/ทิ้งมันเอง (ดู serverCharacters.mapper.ts)
 *
 * หมายเหตุ: model ใน repo จริงเป็นแบบ "anemic" (มีแต่ data ไม่มี method)
 *           logic ไปอยู่ใน use case แทน — ทำได้ แต่ถ้า rule ซับซ้อนขึ้น
 *           ควรย้าย rule มาเป็น method ในนี้ เช่น `markSubmitted(name, now)`
 *           (ดู README หัวข้อ "จุดที่ควรรู้")
 */

/**
 * `pending`   — เราส่งลิงก์ฟอร์มให้ SDK แล้ว
 * `submitted` — SDK แจ้งว่ากรอกฟอร์มแล้ว
 */
export type CharacterFormStatus = 'pending' | 'submitted';

export interface PlayerCharacter {
    characterId: string;
    characterName: string;
    status: CharacterFormStatus;
    createdAt: Date;
    updatedAt: Date;
    submittedAt?: Date;
}

/** 1 record ต่อ (gagaId, gameCode, serverId) */
export class ServerCharacters {
    gagaId: string;
    gameCode: string;
    serverId: string;
    serverName: string;
    characters: PlayerCharacter[];
    createdAt: Date;
    updatedAt: Date;
}
