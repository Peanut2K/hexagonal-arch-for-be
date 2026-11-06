/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → รายชื่อ Mongoose model ทั้งหมด
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: array ที่ส่งให้ MongooseModule.forFeature() ใน adapter.module.ts
 *             เพื่อให้ @InjectModel(...) ใน repository ทำงานได้
 *
 * เพิ่ม collection ใหม่ = เพิ่ม 1 บรรทัดที่นี่
 */
import { ServerCharactersSchema, ServerCharactersSchemaMongo } from './character/schemas/serverCharacters.schema';

export const modelDefinitions = [
    { name: ServerCharactersSchemaMongo.name, schema: ServerCharactersSchema },
    // { name: UserSchemaMongo.name, schema: UserSchema }, ...
];
