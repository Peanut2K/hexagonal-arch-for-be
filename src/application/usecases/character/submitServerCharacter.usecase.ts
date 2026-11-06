/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → USE CASE (ตัวจริงของ business flow)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: 1 class = 1 การกระทำทางธุรกิจ ("ผู้เล่นแจ้งว่ากรอกฟอร์มแล้ว")
 *
 * ข้างในมี:
 *   - constructor : รับ port (interface) ผ่าน DI — ไม่ใช่ class Mongo ตรง ๆ
 *   - handler()   : รับ Command → ทำ rule ธุรกิจ → เรียก port → คืน domain model
 *
 * Flow:
 *   1. หา record ผ่าน port
 *   2. ไม่เจอ draft → โยน AppException (ไม่ใช่ HttpException!)
 *   3. เปลี่ยนสถานะเป็น submitted
 *   4. บันทึกผ่าน port
 *
 * กฎ:
 *   ✅ import ได้: domain/*, ports/*, commands/*, results/*, common/tokens
 *   ❌ ห้าม import: adapter/*, mongoose, express, Request/Response, HttpException
 *
 * ⚠ Trade-off ของ repo นี้: ใช้ @Injectable/@Inject ของ NestJS ใน use case
 *   = framework รั่วเข้า application layer นิดหน่อย (ยอมรับได้เพื่อความสะดวกของ DI)
 *   แต่ logic ไม่ผูกกับ Nest เลย → test ได้ด้วย `new SubmitServerCharacterUseCase(fakeRepo)`
 *   (ดู .spec.ts คู่กัน) — ใน FastAPI จะไม่มีปัญหานี้ เพราะ use case เป็น class เปล่า ๆ
 */
import { Inject, Injectable, Logger } from '@nestjs/common';

import { SERVER_CHARACTERS_REPOSITORY_PORT } from '../../../common/tokens';
import { AppException, ErrorCode } from '../../../domain/errors/errorCodes';
import { ServerCharacters } from '../../../domain/model/serverCharacters.model';
import { SubmitServerCharacterCommand } from '../../commands/character/submitServerCharacterCommand';
import { ServerCharactersRepository } from '../../ports/outbound/character/serverCharacters.repository';

@Injectable()
export class SubmitServerCharacterUseCase {
    private readonly log = new Logger(SubmitServerCharacterUseCase.name);

    constructor(
        // ขอ "ใครก็ได้ที่ implement ServerCharactersRepository" ด้วย token
        // → Nest จะไปดูใน application.providers.ts ว่า token นี้ผูกกับ class ไหน
        @Inject(SERVER_CHARACTERS_REPOSITORY_PORT)
        private readonly serverCharactersRepository: ServerCharactersRepository,
    ) {}

    public async handler(command: SubmitServerCharacterCommand): Promise<ServerCharacters> {
        const server = await this.serverCharactersRepository.findByKey(command);
        const draft = server?.characters.find((c) => c.characterId === command.characterId);
        if (!server || !draft) {
            this.log.warn(`no draft for character_id=${command.characterId}`);
            throw new AppException(ErrorCode.INVALID_REQUEST, 'No identity form was sent for this character.');
        }

        // ── business rule ──
        const now = new Date();
        draft.characterName = command.characterName;
        draft.status = 'submitted';
        draft.submittedAt = now;
        draft.updatedAt = now;
        server.serverName = command.serverName;
        server.updatedAt = now;

        await this.serverCharactersRepository.updateByKeyId(command, server);
        return server;
    }
}
