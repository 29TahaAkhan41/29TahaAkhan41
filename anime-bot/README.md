# 🤖 Anime Bot (Discord)

Türkçe Discord anime botu. Veriler [Jikan](https://jikan.moe) (MyAnimeList) API'sinden gelir — API anahtarı gerekmez.

## Komutlar

| Komut | Açıklama |
|---|---|
| `/anime isim:` | Anime arar; puan, bölüm, tür, stüdyo vb. gösterir. Menüden diğer sonuçlar seçilebilir. |
| `/manga isim:` | Manga arar |
| `/karakter isim:` | Karakter arar |
| `/rastgele` | Rastgele anime önerir |
| `/top kategori:` | En iyi 10 anime (puan, yayında, yakında, popüler, favori) |
| `/sezon` | Bu sezonun animeleri |
| `/takvim gun:` | Günlük yayın takvimi |
| `/yardim` | Komut listesi |

## Kurulum

1. [Discord Developer Portal](https://discord.com/developers/applications)'da **New Application** oluştur.
2. **Bot** sekmesinden token al. **OAuth2 → URL Generator**'da `bot` + `applications.commands` seçip çıkan linkle botu sunucuna ekle.
3. Node.js 18+ kurulu olsun, sonra:

```bash
cd anime-bot
npm install
cp .env.example .env   # DISCORD_TOKEN ve CLIENT_ID değerlerini doldur
npm run deploy         # slash komutlarını kaydeder
npm start
```

> İpucu: `.env` içine `GUILD_ID` (test sunucunun ID'si) yazarsan komutlar anında görünür; boş bırakırsan global kaydedilir (~1 saat).
