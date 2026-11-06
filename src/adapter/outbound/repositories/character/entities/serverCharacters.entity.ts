/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → ENTITY (รูปร่างข้อมูล "ตามที่ DB เก็บ")
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: TypeScript type ของ document ที่ได้จาก Mongo (หลัง `.lean()`)
 *
 * เทียบกับ Domain Model (domain/model/serverCharacters.model.ts):
 *   Entity มี `_id`, `keyId`  ← เรื่องของ DB ล้วน ๆ
 *   Domain ไม่มี              ← ธุรกิจไม่สนว่า DB index ด้วยอะไร
 *
 * ทำไมแยก Entity กับ Schema?
 *   Schema (schemas/) = class มี @Prop decorator ไว้บอก Mongoose ว่าจะสร้าง collection ยังไง
 *   Entity (ไฟล์นี้)  = plain type ไว้ใช้ในโค้ด adapter/mapper ไม่มี magic ของ Mongoose ติดมา
 */
import { Types } from 'mongoose';

import { CharacterFormStatus } from '../../../../../domain/model/serverCharacters.model';

export interface PlayerCharacterEntity {
    characterId: string;
    characterName: string;
    status: CharacterFormStatus;
    createdAt: Date;
    updatedAt: Date;
    submittedAt?: Date;
}

export interface ServerCharactersEntity {
    _id?: Types.ObjectId | string;
    /** `${gagaId}_${gameCode}_${serverId}` — สร้างโดย ServerCharactersMapper.keyId */
    keyId: string;
    gagaId: string;
    gameCode: string;
    serverId: string;
    serverName: string;
    characters: PlayerCharacterEntity[];
    createdAt: Date;
    updatedAt: Date;
}
