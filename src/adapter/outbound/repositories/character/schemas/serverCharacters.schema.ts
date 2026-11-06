/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → OUTBOUND → MONGOOSE SCHEMA
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: นิยาม collection ให้ Mongoose — field, required, enum, index
 *
 * ข้างในมี:
 *   - PlayerCharacterSchemaMongo  : sub-document (ไม่มี _id ของตัวเอง)
 *   - ServerCharactersSchemaMongo : document หลัก
 *   - index ต่าง ๆ                : unique keyId + index สำหรับ query ที่ใช้บ่อย
 *
 * ถูกลงทะเบียนที่ repositories/index.ts → MongooseModule.forFeature(modelDefinitions)
 *
 * ย้ายไป Postgres = ไฟล์นี้ถูกแทนด้วย TypeORM/Prisma model — domain ไม่กระทบ
 * (เทียบ FastAPI: SQLAlchemy model ใน adapters/outbound/persistence/models.py)
 */
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

import { CharacterFormStatus } from '../../../../../domain/model/serverCharacters.model';
import { COLLECTIONS } from '../../../database/mongoCollections';

@Schema({ _id: false })
export class PlayerCharacterSchemaMongo {
    @Prop({ required: true }) characterId: string;
    @Prop({ required: true }) characterName: string;
    @Prop({ required: true, enum: ['pending', 'submitted'] satisfies CharacterFormStatus[] })
    status: CharacterFormStatus;
    @Prop({ type: Date, required: true }) createdAt: Date;
    @Prop({ type: Date, required: true }) updatedAt: Date;
    @Prop({ type: Date, required: false }) submittedAt?: Date;
}

const PlayerCharacterSchema = SchemaFactory.createForClass(PlayerCharacterSchemaMongo);

@Schema({ collection: COLLECTIONS.serverCharacters })
export class ServerCharactersSchemaMongo extends Document {
    @Prop({ required: true }) keyId: string;
    @Prop({ required: true }) gagaId: string;
    @Prop({ required: true }) gameCode: string;
    @Prop({ required: true }) serverId: string;
    @Prop({ required: true }) serverName: string;
    @Prop({ type: [PlayerCharacterSchema], default: [] }) characters: PlayerCharacterSchemaMongo[];
    @Prop({ type: Date, required: true }) createdAt: Date;
    @Prop({ type: Date, required: true }) updatedAt: Date;
}

export const ServerCharactersSchema = SchemaFactory.createForClass(ServerCharactersSchemaMongo);
ServerCharactersSchema.index({ keyId: 1 }, { unique: true }); //   1 record ต่อผู้เล่นต่อ server
ServerCharactersSchema.index({ gagaId: 1, gameCode: 1 }); //       ค้นทุก server ของผู้เล่น 1 คน
ServerCharactersSchema.index({ gameCode: 1, serverId: 1 }); //     list server ของเกม
