/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → INBOUND → PARAM DECORATOR
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: shortcut ให้ controller เขียน `@CurrentUser() user` แทน `req.user`
 *             (ค่าถูกแปะไว้โดย JwtAuthGuard)
 *
 * เทียบ FastAPI: `user: AccessTokenPayload = Depends(get_current_user)`
 */
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

import { AccessTokenPayload } from '../guards/jwtAuth.guard';

export const CurrentUser = createParamDecorator((_: unknown, ctx: ExecutionContext): AccessTokenPayload => {
    return ctx.switchToHttp().getRequest<{ user: AccessTokenPayload }>().user;
});
