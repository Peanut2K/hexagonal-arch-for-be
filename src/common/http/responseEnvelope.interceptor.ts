/**
 * ─────────────────────────────────────────────────────────────────────────
 * COMMON → RESPONSE ENVELOPE INTERCEPTOR (ส่วนหนึ่งของ inbound HTTP adapter)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ห่อทุก response ที่สำเร็จให้อยู่ในรูป
 *             { code: 'OK', message: 'OK', data: <ที่ controller return>, trace_id }
 *
 * controller แค่ `return VnCharacterResponse.toResponse(result)` ไม่ต้องห่อเอง
 * คู่กับ allExceptions.filter.ts (ฝั่ง error) → client เห็นรูปแบบเดียวกันเสมอ
 *
 * ลงทะเบียนที่ adapter.module.ts → { provide: APP_INTERCEPTOR, useClass: ResponseEnvelopeInterceptor }
 */
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Request } from 'express';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { ErrorCode } from '../../domain/errors/errorCodes';

export interface Envelope<T> {
    code: string;
    message: string;
    data?: T;
    trace_id: string;
}

@Injectable()
export class ResponseEnvelopeInterceptor<T> implements NestInterceptor<T, Envelope<T>> {
    intercept(context: ExecutionContext, next: CallHandler): Observable<Envelope<T>> {
        const req = context.switchToHttp().getRequest<Request & { traceId?: string }>();
        return next.handle().pipe(
            map((data) => ({ code: ErrorCode.OK, message: 'OK', data, trace_id: req.traceId ?? '' })),
        );
    }
}
