/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: DOMAIN
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ภาษากลางของ "ความผิดพลาดทางธุรกิจ"
 *
 * ข้างในมี:
 *   - ErrorCode    : enum รหัส error ที่ธุรกิจรู้จัก
 *   - AppException : error ที่ use case โยนออกมา
 *
 * ทำไมอยู่ใน domain:
 *   use case ต้องโยน error ได้ แต่ "ไม่ควรรู้" ว่ามันจะกลายเป็น HTTP 400/404/409
 *   → domain รู้แค่ "INVALID_REQUEST"
 *   → การแปลงเป็น HTTP status อยู่ที่ common/exceptions/errorCodes.ts
 *      และตัวแปลงจริงคือ common/http/allExceptions.filter.ts
 *
 *   ถ้าวันหนึ่งเรียก use case เดียวกันจาก gRPC / CLI / queue consumer
 *   ก็แค่เขียนตัวแปลงใหม่ — use case ไม่ต้องแก้เลย
 */
export enum ErrorCode {
    OK = 'OK',
    INVALID_REQUEST = 'INVALID_REQUEST',
    AUTH_INVALID_TOKEN = 'AUTH_INVALID_TOKEN',
    AUTH_FORBIDDEN = 'AUTH_FORBIDDEN',
    SERVER_ERROR = 'SERVER_ERROR',
}

export class AppException extends Error {
    constructor(
        public readonly errorCode: ErrorCode,
        public readonly overrideMessage?: string,
        public readonly extra?: Record<string, unknown>,
    ) {
        super(overrideMessage ?? errorCode);
    }
}
