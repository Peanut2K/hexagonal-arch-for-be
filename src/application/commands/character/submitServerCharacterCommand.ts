/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → COMMAND (input ของ use case)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: "ใบสั่งงาน" ที่ส่งเข้า use case — เป็น plain object ล้วน ๆ
 *
 * ต่างจาก DTO (adapter/inbound/dtos) ยังไง?
 *   DTO     = รูปร่างตาม HTTP: snake_case, มี @IsString() validator, มาจาก body
 *   Command = รูปร่างตามธุรกิจ: camelCase, ไม่มี decorator, ไม่รู้ว่ามาจาก HTTP
 *
 *   controller เป็นคนแปลง DTO + JWT payload → Command
 *   (ดู IdentityController.characterOf)
 *
 * สังเกต: gagaId / gameCode ไม่ได้มาจาก body แต่มาจาก JWT —
 *          use case ไม่สนว่ามาจากไหน มันรู้แค่ว่า "ต้องมี"
 *
 * คู่ของมันคือ results/ (output ของ use case) — use case ตัวนี้คืน domain model
 * ตรง ๆ เลยไม่มี result file; ถ้า output ต้องรวมหลายอย่าง/ซ่อนบาง field
 * ให้สร้าง application/results/<feature>/<name>Result.ts
 */
export interface SubmitServerCharacterCommand {
    /** มาจาก JWT `sub` */
    readonly gagaId: string;
    /** มาจาก JWT `client_id` */
    readonly gameCode: string;
    readonly serverId: string;
    readonly serverName: string;
    readonly characterId: string;
    readonly characterName: string;
}
