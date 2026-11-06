/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → INBOUND → CONTROLLER (Driving adapter)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: "ปลั๊กขาเข้า" — แปลง HTTP request เป็นการเรียก use case
 *
 * หน้าที่ของ controller มีแค่ 4 อย่าง (ถ้าทำมากกว่านี้ = มี logic รั่วมาแล้ว):
 *   1. รับ input   : @Body() dto (validate แล้วโดย ValidationPipe), @CurrentUser()
 *   2. แปลง        : DTO + JWT → Command               (characterOf / playerOf)
 *   3. เรียก       : useCase.handler(command)
 *   4. แปลงกลับ    : Domain → JSON                     (VnCharacterResponse.toResponse)
 *
 * ❌ ห้ามมีใน controller: query DB, เรียก API ภายนอก, if/else ของ rule ธุรกิจ
 * ✅ inject use case "class" ตรง ๆ ได้เลย (ไม่ต้องมี inbound port interface)
 *    → repo นี้เลือกไม่สร้าง ports/inbound เพราะ use case มี implementation เดียว
 *      สร้าง interface ครอบอีกชั้นก็ไม่ได้อะไรเพิ่ม (ดู README "จุดที่ควรรู้")
 *
 * ถ้าอนาคตมี gRPC / Kafka consumer เรียก use case เดียวกัน
 * → เขียน adapter ใหม่ข้าง ๆ ไฟล์นี้ use case ไม่ต้องแก้
 */
import { Body, Controller, HttpCode, HttpStatus, Post, UseGuards } from '@nestjs/common';

import { SubmitServerCharacterCommand } from '../../../application/commands/character/submitServerCharacterCommand';
import { SubmitServerCharacterUseCase } from '../../../application/usecases/character/submitServerCharacter.usecase';
import { AppException, ErrorCode } from '../../../domain/errors/errorCodes';
import { CurrentUser } from '../decorators/currentUser.decorator';
import { VnCharacterDto } from '../dtos/identityVerification/vnCharacter.dto';
import { AccessTokenPayload, JwtAuthGuard } from '../guards/jwtAuth.guard';
import { VnCharacterResponse } from '../mappers/identityVerification/vnCharacter.response';

@Controller('identity')
export class IdentityController {
    constructor(private readonly submitServerCharacterUseCase: SubmitServerCharacterUseCase) {}

    @UseGuards(JwtAuthGuard)
    @HttpCode(HttpStatus.OK)
    @Post('vn/character')
    async vnCharacter(@CurrentUser() user: AccessTokenPayload, @Body() dto: VnCharacterDto) {
        const player = IdentityController.playerOf(user); //                 1-2. รับ + แปลง
        const result = await this.submitServerCharacterUseCase.handler( //   3.   เรียก
            IdentityController.characterOf(player, dto),
        );
        return VnCharacterResponse.toResponse(result); //                     4.   แปลงกลับ
    }

    /** DTO (snake_case, HTTP) → Command (camelCase, ธุรกิจ) */
    private static characterOf(
        player: { gagaId: string; gameCode: string },
        dto: VnCharacterDto,
    ): SubmitServerCharacterCommand {
        return {
            ...player,
            serverId: dto.server_id,
            serverName: dto.server_name,
            characterId: dto.character_id,
            characterName: dto.character_name,
        };
    }

    /** JWT payload → ตัวตนผู้เล่น (เช็คว่าเป็น token ของผู้เล่น ไม่ใช่ของ server) */
    private static playerOf(user: AccessTokenPayload): { gagaId: string; gameCode: string } {
        if (user.token_use === 'client' || !user.client_id) {
            throw new AppException(ErrorCode.AUTH_FORBIDDEN);
        }
        return { gagaId: user.sub, gameCode: user.client_id };
    }
}
