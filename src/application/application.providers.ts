/**
 * ─────────────────────────────────────────────────────────────────────────
 * COMPOSITION ROOT — "ตู้ปลั๊ก" ที่เสียบ port เข้ากับ adapter
 * ─────────────────────────────────────────────────────────────────────────
 * ไฟล์นี้คือ: ที่เดียวในระบบที่บอกว่า "port X ใช้ adapter Y"
 *
 * ข้างในมี:
 *   - ADAPTER_PROVIDERS : array ของ { provide: TOKEN, useClass: AdapterClass }
 *
 * ทำไมไฟล์นี้ import adapter ได้ ทั้งที่อยู่ในโฟลเดอร์ application?
 *   → เพราะมันไม่ใช่ business logic แต่เป็น "wiring" — ต้องมีสักที่ที่รู้จักทั้งสองฝั่ง
 *     กฎ "application ห้าม import adapter" ใช้กับ usecases/ ports/ commands/ results/
 *     ไม่ใช่กับไฟล์ wiring นี้
 *
 * อยากเปลี่ยน Mongo → Postgres?
 *   เขียน ServerCharactersRepositoryPostgres แล้วแก้แค่บรรทัดเดียวด้านล่าง
 *   use case / controller / test ไม่ต้องแตะเลย  ← นี่คือ point ของ Hexagonal
 *
 * เลือก adapter ตาม config ก็ได้ (repo จริงทำกับ email):
 *   {
 *     provide: EMAIL_SENDER_PORT,
 *     useFactory: (config: ConfigService) =>
 *       config.get('MAIL_TRANSPORT') === 'smtp'
 *         ? new SmtpEmailSenderAdapter(config)   // prod
 *         : new ConsoleEmailSenderAdapter(),     // dev: แค่ log ออก console
 *     inject: [ConfigService],
 *   }
 */
import { Provider } from '@nestjs/common';

import { ServerCharactersRepositoryMongo } from '../adapter/outbound/repositories/character/serverCharacters.repository.mongo';
import { SERVER_CHARACTERS_REPOSITORY_PORT } from '../common/tokens';

export const ADAPTER_PROVIDERS: Provider[] = [
    { provide: SERVER_CHARACTERS_REPOSITORY_PORT, useClass: ServerCharactersRepositoryMongo },
    // { provide: FUNTAP_GATEWAY_PORT, useClass: FuntapGatewayHttp },   ← gateway ไป API ภายนอกก็เป็น port เหมือนกัน
];
