/**
 * ─────────────────────────────────────────────────────────────────────────
 * COMMON → DI TOKENS
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ชื่อ (string) ที่ใช้แทน interface ตอน inject
 *
 * ทำไมต้องมี?
 *   TypeScript interface "หายไป" ตอน compile เป็น JS → Nest เอา interface มาเป็น key ไม่ได้
 *   เลยต้องใช้ string/symbol แทน:
 *     use case     : @Inject(SERVER_CHARACTERS_REPOSITORY_PORT) repo: ServerCharactersRepository
 *     providers.ts : { provide: SERVER_CHARACTERS_REPOSITORY_PORT, useClass: ...Mongo }
 *
 * ทำไมรวมไว้ที่เดียว?
 *   ถ้าประกาศ token ไว้ในไฟล์ port แต่ละไฟล์ จะเกิด import วนระหว่าง ports ↔ adapter
 *   รวมไว้ที่นี่ = หาง่าย + ไม่มี cycle
 *
 * (ใน Python/FastAPI ไม่ต้องมีไฟล์นี้ — Protocol/ABC ยังอยู่ตอน runtime ดู FASTAPI.md)
 */
export const SERVER_CHARACTERS_REPOSITORY_PORT = 'SERVER_CHARACTERS_REPOSITORY_PORT';
export const USERS_REPOSITORY_PORT = 'USERS_REPOSITORY_PORT';
export const EMAIL_SENDER_PORT = 'EMAIL_SENDER_PORT';
export const FUNTAP_GATEWAY_PORT = 'FUNTAP_GATEWAY_PORT';
