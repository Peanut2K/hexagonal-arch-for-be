/**
 * ─────────────────────────────────────────────────────────────────────────
 * ENTRY POINT
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: จุดเริ่มโปรแกรม — สร้าง Nest app, ตั้ง global pipe, เปิด port
 *
 * ValidationPipe:
 *   whitelist  → ตัด field ที่ไม่มีใน DTO ทิ้ง
 *   transform  → แปลง JSON เป็น instance ของ DTO class
 *   = ตัว validate "รูปแบบ" ของ DTO (ดู vnCharacter.dto.ts)
 *
 * repo จริงตั้ง session, CORS, static file, view engine, logger เพิ่มที่นี่
 * (ทั้งหมดเป็นเรื่องของ inbound HTTP — ไม่เกี่ยวกับ domain)
 */
import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';

import { AppModule } from './app.module';

async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.listen(process.env.PORT ?? 3000);
}

void bootstrap();
