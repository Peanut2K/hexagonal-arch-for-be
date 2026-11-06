/**
 * ─────────────────────────────────────────────────────────────────────────
 * LAYER: APPLICATION → NestJS Module
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: กล่องที่รวม use case ทั้งหมด + การผูก port→adapter ไว้ด้วยกัน
 *
 * ข้างในมี:
 *   - providers : USE_CASES + ADAPTER_PROVIDERS → Nest สร้าง instance และ inject ให้
 *   - exports   : USE_CASES → ให้ AdapterModule (ที่มี controller) เอาไปใช้ได้
 *                 + บาง port token ที่ฝั่ง inbound ต้องใช้ตรง ๆ (เช่น guard ต้องเช็ค user)
 */
import { Module } from '@nestjs/common';

import { ADAPTER_PROVIDERS } from './application.providers';
import { USE_CASES } from './application.usecases';

@Module({
    providers: [...USE_CASES, ...ADAPTER_PROVIDERS],
    exports: [...USE_CASES],
})
export class ApplicationModule {}
