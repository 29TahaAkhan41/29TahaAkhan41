import 'dotenv/config';
import { Client, GatewayIntentBits, Events, ActivityType } from 'discord.js';
import { commands } from './commands.js';

const client = new Client({ intents: [GatewayIntentBits.Guilds] });
const byName = new Map(commands.map((c) => [c.data.name, c]));

client.once(Events.ClientReady, (c) => {
  console.log(`✅ ${c.user.tag} olarak giriş yapıldı`);
  c.user.setActivity('anime | /yardim', { type: ActivityType.Watching });
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  const cmd = byName.get(interaction.commandName);
  if (!cmd) return;
  try {
    await interaction.deferReply(); // Jikan bazen 3 saniyeden yavaş cevap veriyor
    await cmd.run(interaction);
  } catch (err) {
    console.error(err);
    const msg = '⚠️ Bir hata oluştu, lütfen biraz sonra tekrar dene.';
    if (interaction.deferred || interaction.replied) await interaction.editReply({ content: msg, embeds: [], components: [] }).catch(() => {});
    else await interaction.reply({ content: msg, ephemeral: true }).catch(() => {});
  }
});

if (!process.env.DISCORD_TOKEN) {
  console.error('DISCORD_TOKEN eksik! .env.example dosyasını .env olarak kopyalayıp doldur.');
  process.exit(1);
}
client.login(process.env.DISCORD_TOKEN);
