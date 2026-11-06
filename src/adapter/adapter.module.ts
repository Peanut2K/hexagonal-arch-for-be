/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: ADAPTER → NestJS Module (รวมทุกอย่างที่แตะโลกภายนอก)
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: กล่องรวม adapter ทั้งขาเข้าและขาออก
 *
 * ข้างในมี:
 *   imports     : ApplicationModule (เพื่อเอา use case มาให้ controller)
 *                 MongooseModule.forRootAsync (เปิด connection)
 *                 MongooseModule.forFeature(modelDefinitions) (ลงทะเบียน model)
 *   controllers : inbound adapter ทั้งหมด (HTTP)
 *   providers   : guard, interceptor ระดับ global
 *   @Global()   : export MongooseModule ให้ repository ใน ApplicationModule ใช้ @InjectModel ได้
 *
 * ลำดับการ import ของ Module:
 *   AppModule → AdapterModule → ApplicationModule
 *   (Nest module graph ≠ dependency rule ของ Hexagonal — อย่าสับสน
 *    dependency rule ดูที่ "ไฟล์ไหน import ไฟล์ไหน" ใน README)
 */
import { Global, Module } from '@nestjs/common';
import { APP_INTERCEPTOR } from '@nestjs/core';
import { JwtModule } from '@nestjs/jwt';
import { MongooseModule } from '@nestjs/mongoose';

import { ApplicationModule } from '../application/application.module';
import { ResponseEnvelopeInterceptor } from '../common/http/responseEnvelope.interceptor';
import { IdentityController } from './inbound/controllers/identity.controller';
import { JwtAuthGuard } from './inbound/guards/jwtAuth.guard';
import { modelDefinitions } from './outbound/repositories';

@Global()
@Module({
    imports: [
        ApplicationModule,
        JwtModule.register({ secret: process.env.JWT_SECRET ?? 'dev-only' }),
        MongooseModule.forRootAsync({ useFactory: () => ({ uri: process.env.MONGODB_URI }) }),
        MongooseModule.forFeature(modelDefinitions),
    ],
    controllers: [IdentityController],
    providers: [{ provide: APP_INTERCEPTOR, useClass: ResponseEnvelopeInterceptor }, JwtAuthGuard],
    exports: [MongooseModule],
})
export class AdapterModule {}
