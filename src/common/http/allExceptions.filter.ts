/**
 * ─────────────────────────────────────────────────────────────────────────
 * COMMON → GLOBAL EXCEPTION FILTER (ส่วนหนึ่งของ inbound HTTP adapter)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ตัวดักทุก error ที่หลุดออกมา แล้วแปลงเป็น HTTP response มาตรฐาน
 *
 *   use case โยน AppException(INVALID_REQUEST)
 *        ↓
 *   filter นี้ดักได้ → ดูตาราง ERROR_STATUS_MAP → ตอบ 400 { code, message, data, trace_id }
 *
 * ทำให้ use case ไม่ต้องรู้จัก HttpException / status code เลย
 * error ที่ไม่รู้จัก → 500 และ "ไม่ส่ง stack trace ออกไป"
 *
 * ลงทะเบียนที่ app.module.ts → { provide: APP_FILTER, useClass: AllExceptionsFilter }
 */
import { ArgumentsHost, Catch, ExceptionFilter, HttpException, Logger } from '@nestjs/common';
import { Request, Response } from 'express';

import { AppException, ErrorCode } from '../../domain/errors/errorCodes';
import { ERROR_MESSAGE_MAP, ERROR_STATUS_MAP } from '../exceptions/errorCodes';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
    private readonly logger = new Logger('ExceptionFilter');

    catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const res = ctx.getResponse<Response>();
        const traceId = ctx.getRequest<Request & { traceId?: string }>().traceId ?? '';

        if (exception instanceof AppException) {
            res.status(ERROR_STATUS_MAP[exception.errorCode]).json({
                code: exception.errorCode,
                message: exception.overrideMessage ?? ERROR_MESSAGE_MAP[exception.errorCode],
                data: exception.extra,
                trace_id: traceId,
            });
            return;
        }

        // Nest เอง (เช่น ValidationPipe โยน BadRequestException) → แปลงเป็น envelope เดียวกัน
        if (exception instanceof HttpException) {
            res.status(exception.getStatus()).json({
                code: ErrorCode.INVALID_REQUEST,
                message: exception.message,
                trace_id: traceId,
            });
            return;
        }

        this.logger.error(exception);
        res.status(500).json({
            code: ErrorCode.SERVER_ERROR,
            message: ERROR_MESSAGE_MAP[ErrorCode.SERVER_ERROR],
            trace_id: traceId,
        });
    }
}
