import { SlashCommandBuilder, ActionRowBuilder, StringSelectMenuBuilder, ComponentType } from 'discord.js';
import * as jikan from './jikan.js';
import { animeEmbed, mangaEmbed, characterEmbed, listEmbed } from './embeds.js';

const DAYS = [
  ['monday', 'Pazartesi'], ['tuesday', 'Salı'], ['wednesday', 'Çarşamba'], ['thursday', 'Perşembe'],
  ['friday', 'Cuma'], ['saturday', 'Cumartesi'], ['sunday', 'Pazar'],
];

// Birden çok sonuç varsa ilkini gösterip, açılır menüden başka birini seçtirir.
async function showWithPicker(interaction, results, toEmbed, label) {
  if (!results.length) {
    return interaction.editReply(`❌ "${interaction.options.getString('isim')}" için ${label} bulunamadı.`);
  }
  const menu = new StringSelectMenuBuilder()
    .setCustomId('pick')
    .setPlaceholder('Başka bir sonuç seç…')
    .addOptions(
      results.slice(0, 10).map((r, i) => ({
        label: (r.title ?? r.name).slice(0, 100),
        description: String(r.type ?? (r.favorites != null ? `❤️ ${r.favorites}` : '')).slice(0, 100) || undefined,
        value: String(i),
      })),
    );
  const row = new ActionRowBuilder().addComponents(menu);
  const msg = await interaction.editReply({
    embeds: [toEmbed(results[0])],
    components: results.length > 1 ? [row] : [],
  });
  if (results.length < 2) return;

  const collector = msg.createMessageComponentCollector({ componentType: ComponentType.StringSelect, time: 120_000 });
  collector.on('collect', async (i) => {
    if (i.user.id !== interaction.user.id) {
      return i.reply({ content: 'Bu menü sadece komutu kullanan kişi için. 🙂', ephemeral: true });
    }
    await i.update({ embeds: [toEmbed(results[Number(i.values[0])])] });
  });
  collector.on('end', () => interaction.editReply({ components: [] }).catch(() => {}));
}

export const commands = [
  {
    data: new SlashCommandBuilder()
      .setName('anime').setDescription('Anime ara')
      .addStringOption((o) => o.setName('isim').setDescription('Anime adı').setRequired(true)),
    async run(i) {
      await showWithPicker(i, await jikan.searchAnime(i.options.getString('isim')), animeEmbed, 'anime');
    },
  },
  {
    data: new SlashCommandBuilder()
      .setName('manga').setDescription('Manga ara')
      .addStringOption((o) => o.setName('isim').setDescription('Manga adı').setRequired(true)),
    async run(i) {
      await showWithPicker(i, await jikan.searchManga(i.options.getString('isim')), mangaEmbed, 'manga');
    },
  },
  {
    data: new SlashCommandBuilder()
      .setName('karakter').setDescription('Anime/manga karakteri ara')
      .addStringOption((o) => o.setName('isim').setDescription('Karakter adı').setRequired(true)),
    async run(i) {
      await showWithPicker(i, await jikan.searchCharacter(i.options.getString('isim')), characterEmbed, 'karakter');
    },
  },
  {
    data: new SlashCommandBuilder().setName('rastgele').setDescription('Rastgele bir anime öner'),
    async run(i) {
      const a = await jikan.randomAnime();
      await i.editReply({ content: '🎲 İşte sana rastgele bir anime:', embeds: [animeEmbed(a)] });
    },
  },
  {
    data: new SlashCommandBuilder()
      .setName('top').setDescription('En iyi 10 anime')
      .addStringOption((o) =>
        o.setName('kategori').setDescription('Liste türü').addChoices(
          { name: 'En yüksek puan', value: 'score' },
          { name: 'Şu an yayında', value: 'airing' },
          { name: 'Yakında', value: 'upcoming' },
          { name: 'En popüler', value: 'bypopularity' },
          { name: 'En çok favorilenen', value: 'favorite' },
        )),
    async run(i) {
      const k = i.options.getString('kategori') ?? 'score';
      const list = await jikan.topAnime(k === 'score' ? null : k);
      await i.editReply({
        embeds: [listEmbed('🏆 En İyi Animeler', list, (a) => `— ⭐ ${a.score ?? '?'} • ${a.type ?? ''}`)],
      });
    },
  },
  {
    data: new SlashCommandBuilder().setName('sezon').setDescription('Bu sezon yayınlanan animeler'),
    async run(i) {
      const list = (await jikan.seasonNow()).sort((a, b) => (b.members ?? 0) - (a.members ?? 0));
      await i.editReply({ embeds: [listEmbed('🌸 Bu Sezonun Animeleri', list, (a) => `— ⭐ ${a.score ?? '?'}`)] });
    },
  },
  {
    data: new SlashCommandBuilder()
      .setName('takvim').setDescription('Bugün (veya seçilen gün) yayınlanan animeler')
      .addStringOption((o) =>
        o.setName('gun').setDescription('Gün').addChoices(...DAYS.map(([value, name]) => ({ name, value })))),
    async run(i) {
      const today = DAYS[(new Date().getDay() + 6) % 7][0];
      const day = i.options.getString('gun') ?? today;
      const list = await jikan.schedule(day);
      const dayName = DAYS.find(([v]) => v === day)[1];
      await i.editReply({
        embeds: [listEmbed(`📅 ${dayName} Yayın Takvimi`, list, (a) => `— 🕒 ${a.broadcast?.time ?? '?'} (JST)`)],
      });
    },
  },
  {
    data: new SlashCommandBuilder().setName('yardim').setDescription('Komut listesini göster'),
    async run(i) {
      const lines = commands.map((c) => `\`/${c.data.name}\` — ${c.data.description}`);
      await i.editReply({ content: `**🤖 Anime Bot Komutları**\n${lines.join('\n')}` });
    },
  },
];
