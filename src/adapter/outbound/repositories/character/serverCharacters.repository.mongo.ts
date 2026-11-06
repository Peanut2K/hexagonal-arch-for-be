/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → REPOSITORY (Driven adapter)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: "ปลั๊กตัวผู้" ที่เสียบเข้ากับ port ServerCharactersRepository
 *             — implementation จริงที่คุยกับ MongoDB
 *
 * ข้างในมี:
 *   - `implements ServerCharactersRepository` → compiler บังคับว่า method ครบตาม port
 *   - inject Mongoose Model ผ่าน @InjectModel
 *   - ทุก method: query Mongo → ได้ Entity → Mapper.toDomain → คืน Domain
 *
 * กฎ:
 *   ✅ ที่นี่เท่านั้นที่ import mongoose ได้
 *   ✅ ซ่อน detail ของ DB ทั้งหมด (keyId, aggregate, lean, cache)
 *   ❌ ห้ามมี rule ธุรกิจ (เช่น "ต้องเป็น pending ก่อนถึง submit ได้") — นั่นของ use case
 *
 * 💡 repo จริงมี Redis cache อยู่ "ใน" adapter นี้ (get cache → miss → query → set cache,
 *    และ invalidate ตอน create/update) — use case ไม่รู้เลยว่ามี cache
 *    นี่คืออีกข้อดีของ port: เพิ่ม cache / retry / metrics ได้โดยไม่แตะ business logic
 *    (skeleton นี้ตัด cache ออกเพื่อให้อ่านง่าย)
 */
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';

import {
    GameServer,
    ServerCharactersRepository,
    ServerKey,
} from '../../../../application/ports/outbound/character/serverCharacters.repository';
import { ServerCharacters } from '../../../../domain/model/serverCharacters.model';
import { ServerCharactersMapper } from '../../mappers/character/serverCharacters.mapper';
import { ServerCharactersEntity } from './entities/serverCharacters.entity';
import { ServerCharactersSchemaMongo } from './schemas/serverCharacters.schema';

@Injectable()
export class ServerCharactersRepositoryMongo implements ServerCharactersRepository {
    constructor(@InjectModel(ServerCharactersSchemaMongo.name) private readonly model: Model<ServerCharactersEntity>) {}

    public async findByKey(key: ServerKey): Promise<ServerCharacters | undefined> {
        const doc = await this.model.findOne({ keyId: ServerCharactersMapper.keyId(key) }).lean<ServerCharactersEntity>().exec();
        return doc ? ServerCharactersMapper.toDomain(doc) : undefined;
    }

    public async findByGagaId(gagaId: string, gameCode: string): Promise<ServerCharacters[]> {
        const docs = await this.model.find({ gagaId, gameCode }).lean<ServerCharactersEntity[]>().exec();
        return docs.map(ServerCharactersMapper.toDomain);
    }

    public async findServersByGameCode(gameCode: string): Promise<GameServer[]> {
        const rows = await this.model
            .aggregate<{ _id: string; serverName: string }>([
                { $match: { gameCode } },
                { $group: { _id: '$serverId', serverName: { $first: '$serverName' } } },
            ])
            .exec();
        return rows.map((r) => ({ serverId: r._id, serverName: r.serverName }));
    }

    public async create(server: ServerCharacters): Promise<void> {
        await this.model.create(ServerCharactersMapper.toEntity(server));
    }

    public async updateByKeyId(key: ServerKey, server: ServerCharacters): Promise<void> {
        await this.model
            .updateOne({ keyId: ServerCharactersMapper.keyId(key) }, { $set: ServerCharactersMapper.toEntity(server) })
            .exec();
    }
}
