/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → INBOUND → GUARD (authentication)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ด่านตรวจก่อนเข้า controller — อ่าน `Authorization: Bearer <jwt>`
 *             ตรวจลายเซ็น แล้วแปะ payload ไว้ที่ `req.user`
 *
 * ทำไมอยู่ฝั่ง adapter/inbound?
 *   เพราะ "Bearer header" เป็นเรื่องของ HTTP — use case ไม่ควรรู้จัก header
 *   use case รับแค่ gagaId ที่ผ่านการยืนยันมาแล้ว (ผ่าน Command)
 *
 * สังเกต: guard ใน repo จริงเรียก USERS_REPOSITORY_PORT เพื่อเช็คว่า user ยังอยู่
 *          → inbound adapter ใช้ port ได้ (ผ่าน token) แต่ไม่ import Mongo class ตรง ๆ
 *          (ใน skeleton นี้ตัดส่วนนั้นออกเพื่อความสั้น)
 *
 * ใช้คู่กับ decorators/currentUser.decorator.ts
 */
import { CanActivate, ExecutionContext, Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Request } from 'express';

import { AppException, ErrorCode } from '../../../domain/errors/errorCodes';

export interface AccessTokenPayload {
    sub: string;
    client_id?: string;
    scope?: string;
    token_use?: string;
}

@Injectable()
export class JwtAuthGuard implements CanActivate {
    constructor(private readonly jwtService: JwtService) {}

    canActivate(context: ExecutionContext): boolean {
        const req = context.switchToHttp().getRequest<Request & { user?: AccessTokenPayload }>();
        const authHeader = req.header('authorization');
        if (!authHeader?.startsWith('Bearer ')) {
            throw new AppException(ErrorCode.AUTH_INVALID_TOKEN);
        }
        try {
            req.user = this.jwtService.verify<AccessTokenPayload>(authHeader.slice('Bearer '.length).trim());
        } catch {
            throw new AppException(ErrorCode.AUTH_INVALID_TOKEN);
        }
        return true;
    }
}
