/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → รายชื่อ use case ทั้งหมด
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: array ของ use case class ทุกตัว ให้ ApplicationModule ลงทะเบียนเป็น provider
 *             และ export ออกไปให้ controller (ฝั่ง adapter) inject ได้
 *
 * เพิ่ม use case ใหม่ = เพิ่ม 1 บรรทัดที่นี่ (repo จริงมี ~100 ตัว)
 */
import { SubmitServerCharacterUseCase } from './usecases/character/submitServerCharacter.usecase';

export const USE_CASES = [
    SubmitServerCharacterUseCase,
    // ...use case อื่น ๆ
];
