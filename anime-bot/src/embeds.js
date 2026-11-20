import { EmbedBuilder } from 'discord.js';

const COLOR = 0x2e51a2; // MyAnimeList mavisi

const STATUS_TR = {
  'Finished Airing': 'Tamamlandı',
  'Currently Airing': 'Yayında',
  'Not yet aired': 'Henüz yayınlanmadı',
  Finished: 'Tamamlandı',
  Publishing: 'Yayınlanıyor',
  'On Hiatus': 'Ara verildi',
  Discontinued: 'Durduruldu',
  'Not yet published': 'Henüz yayınlanmadı',
};

export function trim(text, max = 1000) {
  if (!text) return 'Açıklama yok.';
  const clean = text.replace(/\[Written by MAL Rewrite\]/g, '').trim();
  return clean.length > max ? clean.slice(0, max - 1) + '…' : clean;
}

const names = (arr) => (arr?.length ? arr.map((x) => x.name).join(', ') : '—');
const num = (n) => (n == null ? '—' : n.toLocaleString('tr-TR'));

export function animeEmbed(a) {
  return new EmbedBuilder()
    .setColor(COLOR)
    .setTitle(a.title)
    .setURL(a.url)
    .setThumbnail(a.images?.jpg?.large_image_url ?? null)
    .setDescription(trim(a.synopsis))
    .addFields(
      { name: '⭐ Puan', value: a.score ? `${a.score} / 10` : '—', inline: true },
      { name: '🏆 Sıralama', value: a.rank ? `#${a.rank}` : '—', inline: true },
      { name: '📺 Tür', value: a.type ?? '—', inline: true },
      { name: '🎞️ Bölüm', value: String(a.episodes ?? '?'), inline: true },
      { name: '📡 Durum', value: STATUS_TR[a.status] ?? a.status ?? '—', inline: true },
      { name: '📅 Yıl', value: String(a.year ?? a.aired?.prop?.from?.year ?? '—'), inline: true },
      { name: '🏷️ Türler', value: names(a.genres) },
      { name: '🎬 Stüdyo', value: names(a.studios), inline: true },
      { name: '👥 Üye', value: num(a.members), inline: true },
    )
    .setFooter({ text: `${a.title_japanese ?? ''} • MyAnimeList` });
}

export function mangaEmbed(m) {
  return new EmbedBuilder()
    .setColor(COLOR)
    .setTitle(m.title)
    .setURL(m.url)
    .setThumbnail(m.images?.jpg?.large_image_url ?? null)
    .setDescription(trim(m.synopsis))
    .addFields(
      { name: '⭐ Puan', value: m.score ? `${m.score} / 10` : '—', inline: true },
      { name: '🏆 Sıralama', value: m.rank ? `#${m.rank}` : '—', inline: true },
      { name: '📖 Tür', value: m.type ?? '—', inline: true },
      { name: '📚 Cilt', value: String(m.volumes ?? '?'), inline: true },
      { name: '📄 Bölüm', value: String(m.chapters ?? '?'), inline: true },
      { name: '📡 Durum', value: STATUS_TR[m.status] ?? m.status ?? '—', inline: true },
      { name: '🏷️ Türler', value: names(m.genres) },
      { name: '✍️ Yazar', value: names(m.authors) },
    )
    .setFooter({ text: 'MyAnimeList' });
}

export function characterEmbed(c) {
  return new EmbedBuilder()
    .setColor(COLOR)
    .setTitle(c.name + (c.name_kanji ? ` (${c.name_kanji})` : ''))
    .setURL(c.url)
    .setImage(c.images?.jpg?.image_url ?? null)
    .setDescription(trim(c.about, 1500))
    .addFields(
      { name: '❤️ Favori', value: num(c.favorites), inline: true },
      { name: '🔖 Takma adlar', value: c.nicknames?.length ? c.nicknames.slice(0, 5).join(', ') : '—', inline: true },
    )
    .setFooter({ text: 'MyAnimeList' });
}

export function listEmbed(title, items, describe) {
  const lines = items.map((x, i) => `**${i + 1}.** [${x.title}](${x.url}) ${describe(x)}`);
  return new EmbedBuilder()
    .setColor(COLOR)
    .setTitle(title)
    .setDescription(lines.join('\n').slice(0, 4000) || 'Sonuç bulunamadı.')
    .setThumbnail(items[0]?.images?.jpg?.image_url ?? null)
    .setFooter({ text: 'MyAnimeList' });
}
