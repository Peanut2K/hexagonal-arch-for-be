/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → DATABASE CONSTANTS
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ชื่อ collection ทั้งหมดใน Mongo รวมไว้ที่เดียว
 *             (รายละเอียดของ DB → อยู่ฝั่ง adapter เท่านั้น domain ไม่เคยเห็น)
 */
export const COLLECTIONS = {
    users: 'users',
    serverCharacters: 'server_characters',
} as const;
