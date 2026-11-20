// Slash komutlarını Discord'a kaydeder. Komutları değiştirdiğinde bir kez çalıştır: npm run deploy
import 'dotenv/config';
import { REST, Routes } from 'discord.js';
import { commands } from './commands.js';

const { DISCORD_TOKEN, CLIENT_ID, GUILD_ID } = process.env;
if (!DISCORD_TOKEN || !CLIENT_ID) {
  console.error('DISCORD_TOKEN ve CLIENT_ID .env içinde olmalı.');
  process.exit(1);
}

const rest = new REST().setToken(DISCORD_TOKEN);
const body = commands.map((c) => c.data.toJSON());
const route = GUILD_ID
  ? Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID) // anında görünür
  : Routes.applicationCommands(CLIENT_ID); // tüm sunucular (yayılması ~1 saat sürebilir)

await rest.put(route, { body });
console.log(`✅ ${body.length} komut ${GUILD_ID ? 'sunucuya' : 'global olarak'} kaydedildi.`);
