/**
 * ─────────────────────────────────────────────────────────────────────────
 * COMMON → ตาราง ErrorCode (domain) → HTTP status / message
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: สะพานระหว่าง "ภาษาธุรกิจ" กับ "ภาษา HTTP"
 *
 * domain รู้แค่ ErrorCode.INVALID_REQUEST
 * ไฟล์นี้บอกว่า INVALID_REQUEST = HTTP 400 + ข้อความนี้
 *
 * `Record<ErrorCode, number>` บังคับให้ทุก code มี status
 * → เพิ่ม code ใหม่ใน domain แล้วลืมเพิ่มที่นี่ = compile ไม่ผ่าน
 */
import { ErrorCode } from '../../domain/errors/errorCodes';

export const ERROR_STATUS_MAP: Record<ErrorCode, number> = {
    [ErrorCode.OK]: 200,
    [ErrorCode.INVALID_REQUEST]: 400,
    [ErrorCode.AUTH_INVALID_TOKEN]: 401,
    [ErrorCode.AUTH_FORBIDDEN]: 403,
    [ErrorCode.SERVER_ERROR]: 500,
};

export const ERROR_MESSAGE_MAP: Record<ErrorCode, string> = {
    [ErrorCode.OK]: 'OK',
    [ErrorCode.INVALID_REQUEST]: 'The request is missing or has invalid fields.',
    [ErrorCode.AUTH_INVALID_TOKEN]: 'The access token is missing, invalid, or expired.',
    [ErrorCode.AUTH_FORBIDDEN]: 'You do not have permission to perform this action.',
    [ErrorCode.SERVER_ERROR]: 'Something went wrong.',
};
