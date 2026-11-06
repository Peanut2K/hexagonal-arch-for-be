/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → UNIT TEST ของ use case
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ตัวพิสูจน์ว่า Hexagonal "คุ้ม"
 *
 * สังเกต:
 *   - ไม่มี Mongo, ไม่มี Nest TestingModule, ไม่มี HTTP
 *   - แค่ fake object 2 method ที่หน้าตาตรงกับ port → `new UseCase(fake)` → จบ
 *   - test รันเป็น ms เพราะ use case พึ่งแค่ interface
 *
 * ถ้าวันหนึ่ง test แบบนี้เขียนยาก (ต้อง mock mongoose, express)
 * = สัญญาณว่า use case ไป import ของ adapter มาแล้ว → layer รั่ว
 */
import { AppException, ErrorCode } from '../../../domain/errors/errorCodes';
import { PlayerCharacter, ServerCharacters } from '../../../domain/model/serverCharacters.model';
import { ServerCharactersRepository } from '../../ports/outbound/character/serverCharacters.repository';
import { SubmitServerCharacterUseCase } from './submitServerCharacter.usecase';

const COMMAND = {
    gagaId: 'VNGG000000000000',
    gameCode: 'excalibur',
    serverId: '2',
    serverName: 'S2',
    characterId: '1002',
    characterName: 'DDH33',
};

describe('SubmitServerCharacterUseCase', () => {
    const build = (characters?: Partial<PlayerCharacter>[]) => {
        const repo = {
            findByKey: jest.fn().mockResolvedValue(characters && ({ characters } as ServerCharacters)),
            updateByKeyId: jest.fn().mockResolvedValue(undefined),
        };
        return { usecase: new SubmitServerCharacterUseCase(repo as unknown as ServerCharactersRepository), repo };
    };

    it('moves the draft to submitted and saves the record', async () => {
        const { usecase, repo } = build([
            { characterId: '9999', status: 'pending' },
            { characterId: '1002', characterName: 'old', status: 'pending' },
        ]);

        const saved = await usecase.handler(COMMAND);

        expect(saved.characters[1]).toMatchObject({ characterName: 'DDH33', status: 'submitted' });
        expect(saved.characters[0].status).toBe('pending');
        expect(repo.updateByKeyId).toHaveBeenCalledWith(COMMAND, saved);
    });

    it('rejects when there is no draft', async () => {
        const { usecase, repo } = build(undefined);
        const error = await usecase.handler(COMMAND).catch((e: unknown) => e);
        expect((error as AppException).errorCode).toBe(ErrorCode.INVALID_REQUEST);
        expect(repo.updateByKeyId).not.toHaveBeenCalled();
    });
});
