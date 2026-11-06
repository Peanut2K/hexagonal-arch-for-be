/**
 * ─────────────────────────────────────────────────────────────────────────
 * ROOT MODULE
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: module บนสุด — import AdapterModule (ซึ่ง import ApplicationModule ต่ออีกที)
 *             + ลงทะเบียน global exception filter
 *
 * repo จริงมี ConfigModule, LoggerModule, RedisCacheModule, middleware เพิ่มที่นี่ด้วย
 */
import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';

import { AdapterModule } from './adapter/adapter.module';
import { AllExceptionsFilter } from './common/http/allExceptions.filter';

@Module({
    imports: [AdapterModule],
    providers: [{ provide: APP_FILTER, useClass: AllExceptionsFilter }],
})
export class AppModule {}
