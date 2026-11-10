# Çınarköy — Stardew Valley için yeni köy modu

Stardew Valley **1.6+** için bir [Content Patcher](https://www.nexusmods.com/stardewvalley/mods/1915)
içerik paketi. Oyuna vagonla (minecart) gidilen yeni bir köy haritası ekler.
C# gerekmez; her şey JSON + Tiled haritası.

![Harita önizlemesi](onizleme.png)

## Kurulum

1. [SMAPI](https://smapi.io) ve Content Patcher'ı kur.
2. `[CP] Cinarkoy` klasörünü oyunun `Mods` klasörüne kopyala.
3. Oyunu SMAPI ile başlat.

## Köye gitmek

- **Yürüyerek:** çiftlikten otobüs durağına çık; birkaç adım ileride, yolun
  üst kenarındaki çimde ok işaretli bir tabela durur. Tabelaya tıkla.
- **Vagonla:** herhangi bir vagona tıkla, listeden *Çınarköy*'ü seç.
  (Vagonların açık olması gerekir: Topluluk Merkezi kazan dairesi ya da Joja.)
- **Test için:** SMAPI konsoluna şunu yaz:

  ```
  debug warp TahaAkhan.Cinarkoy_Koy 10 22
  ```

Dönüş için köydeki tabelaya (otobüs durağına) ya da vagona tıkla.

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `[CP] Cinarkoy/manifest.json` | Modun kimliği |
| `[CP] Cinarkoy/content.json` | Konum kaydı, vagon durağı, harita yüklemesi |
| `[CP] Cinarkoy/assets/Cinarkoy.tmx` | Köy haritası ([Tiled](https://www.mapeditor.org) ile düzenlenir) |
| `[CP] Cinarkoy/assets/Tabela.tmx` | Otobüs durağına bindirilen tabela yaması |
| `[CP] Cinarkoy/i18n/` | Çeviriler (`default.json` İngilizce, `tr.json` Türkçe) |
| `tools/harita_uret.py` | Haritayı oyunun kendi karolarından üreten betik |

## Haritayı düzenlemek

Harita oyunun kendi karo setlerini (`spring_town`, `spring_outdoorsTileSheet` …)
kullanır; bu görseller moda dahil değildir, oyun onları kendi dosyalarından yükler.
Mevsim değişince karolar da kendiliğinden değişir.

`Cinarkoy.tmx` dosyasını [Tiled](https://www.mapeditor.org) ile açmak için karo
seti PNG'leri aynı klasörde olmalı: oyunu
[StardewXnbHack](https://github.com/Pathoschild/StardewXnbHack) ile aç, haritayı
`Content (unpacked)/Maps` klasörüne kopyalayıp orada düzenle, bitince yalnızca
`.tmx` dosyasını geri getir. **Oyunun PNG'lerini bu depoya ya da moda koyma.**

Katman adları oyun için anlamlıdır, değiştirme:

- `Back` — zemin (üzerinde yürünür)
- `Buildings` — engeller (duvar, ağaç gövdesi)
- `Front` / `AlwaysFront` — oyuncunun önünde çizilenler (çatılar, ağaç tepeleri)

Vagonun (6, 20), tabelanın (10, 21) ve varış karolarının (6, 22) / (10, 22) yerini
değiştirirsen `content.json` içindeki koordinatları da güncelle.

Haritayı baştan üretmek için:

```
python3 tools/harita_uret.py "<oyun klasörü>/Content (unpacked)/Maps"
```

Betik evleri, ağaçları, vagonu ve tabelayı oyunun `Town.tmx` / `BusStop.tmx`
haritalarından okur. Haritayı elle düzenlemeye başladıktan sonra tekrar
çalıştırma; haritanın üzerine yazar.

## Sırada ne var

- Evlerin içleri (her ev için ayrı harita + kapı `Warp`'ları)
- Köylüler (`Data/Characters`, portre ve sprite çizimleri, diyaloglar, programlar)
- Dükkân (`Data/Shops`)
- Tabela yerine gerçek bir yürüyüş yolu (vanilla bir haritanın kenarına `AddWarps`)
- Dünya haritasında köyün görünmesi (`Data/WorldMap`)
