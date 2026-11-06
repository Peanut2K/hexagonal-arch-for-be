/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → INBOUND → DTO (Request body)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: รูปร่างของ JSON body ที่ client ส่งมา + กฎ validate ระดับ "รูปแบบ"
 *
 * ข้างในมี:
 *   - field เป็น snake_case ตาม API contract (ไม่ใช่ตามโค้ดภายใน)
 *   - decorator ของ class-validator → ValidationPipe (ใน main.ts) เช็คให้อัตโนมัติ
 *     body ผิด → 400 ก่อนถึง controller ด้วยซ้ำ
 *
 * Validate 2 ระดับ (สำคัญ!):
 *   DTO      : "รูปแบบถูกไหม" — เป็น string? ยาวไม่เกิน 64? ไม่ว่าง?
 *   Use case : "ถูกตามธุรกิจไหม" — มี draft ของตัวละครนี้จริงไหม?
 *   อย่าเอา rule ธุรกิจมาไว้ใน DTO และอย่าเช็ค type ซ้ำใน use case
 *
 * DTO ไม่เคยถูกส่งเข้า use case ตรง ๆ — controller แปลงเป็น Command ก่อนเสมอ
 */
import { IsNotEmpty, IsString, MaxLength } from 'class-validator';

/** POST /identity/vn/character */
export class VnCharacterDto {
    @IsString()
    @IsNotEmpty()
    @MaxLength(64)
    server_id: string;

    @IsString()
    @IsNotEmpty()
    @MaxLength(64)
    server_name: string;

    @IsString()
    @IsNotEmpty()
    @MaxLength(64)
    character_id: string;

    @IsString()
    @IsNotEmpty()
    @MaxLength(64)
    character_name: string;
}
