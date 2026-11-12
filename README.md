# Lumina

NeoForge **1.21.1** için yıldız ışığı modu. Gece gökyüzünden ışık toplar, bu ışığı ışınlarla
bloktan bloğa aktarır ve kaidelerde eşyalara işlersin. Astral Sorcery'deki yıldız ışığı
fikrinden esinlenmiştir; kod, isimler ve dokular bu moda özgüdür.

> Depodaki `assets/astralsorcery/lang/tr_tr.json` ayrı bir iştir (Astral Sorcery Türkçe çevirisi)
> ve Lumina jar'ına dahil edilmez.

## Nasıl çalışır

**1. Toplama.** *Yıldız Işığı Toplayıcı* üstü açık gökyüzüne bakıyorsa geceleri ışık biriktirir.
Yoğunluk şu çarpanların çarpımıdır:

| Etken | Değer |
| --- | --- |
| Gece saati | Gün batımından sonra yükselir, gece yarısı %100, gün doğarken söner; gündüz 0 |
| Ay evresi | Yeni ay %60 → dolunay %100 |
| Yükseklik | y=40 ve altı %50 → y=200 ve üstü %100 |
| Hava | Açık %100, yağmur %50, fırtına %25 |

Tam yoğunlukta tick başına 4 birim toplanır. Gökyüzü olmayan boyutlarda (Nether, End) çalışmaz.

**2. Aktarma.** *Bağlama Asası* ile önce kaynağa, sonra hedefe tıklayarak ışın kurarsın.
Işınlar en fazla 16 blok gider, blok başına %1,5 ışık kaybeder; cam gibi saydam bloklardan
geçer, opak tam bloklar ışını keser. Eğilerek tıklamak bloğun ışınlarını siler; asayı boşlukta
kullanmak bulunduğun yerdeki yoğunluğu gösterir.

| Blok | Kapasite | Işın sayısı | Görev |
| --- | --- | --- | --- |
| Yıldız Işığı Toplayıcı | 2000 | 1 | Gökyüzünden ışık toplar |
| Aktarım Merceği | 400 | 1 | Işını başka yöne çevirir |
| Ayırıcı Prizma | 400 | 3 | Işığı ışınlara eşit böler |
| Yıldız Işığı Haznesi | 20000 | 1 | Gündüz için ışık depolar |
| İşleme Kaidesi | 400 | – | Işığı eşyaya işler |

Boş elle tıklamak bloğun doluluğunu gösterir; hepsi karşılaştırıcıya (comparator) sinyal verir.

**3. İşleme.** *İşleme Kaidesi*'ne eşya koy (sağ tık), ışın gönder; gereken ışık dolunca eşya
dönüşür. Huniler kaideye eşya koyabilir ve yalnızca biten eşyayı çekebilir.

| Girdi | Çıktı | Yıldız ışığı |
| --- | --- | --- |
| Lümen Parçası | Yüklü Lümen Parçası | 250 |
| Demir Külçe | Yıldız Işıklı Külçe | 400 |
| Kızıltaş | Parıltı Taşı Tozu | 150 |
| Kuvars | Ametist Parçası | 300 |
| Kırık Taş | End Taşı | 200 |
| Parıltı Taşı | Deniz Feneri | 600 |
| Cam Şişe | Tecrübe Şişesi | 1200 |

Yeni tarif eklemek için veri paketine `lumina:infusion` türünde bir dosya koymak yeterli:

```json
{
  "type": "lumina:infusion",
  "ingredient": { "item": "minecraft:iron_ingot" },
  "result": { "id": "lumina:starlit_ingot", "count": 1 },
  "starlight": 400
}
```

**Başlangıç.** *Lümen Cevheri* Overworld'de y=-32 ile 160 arasında çıkar (demir kazma gerekir).
Parçalardan asa, cilalı mercek, toplayıcı, mercek ve kaide üretilir; prizma ve hazne için önce
kaidede yüklü parça ve yıldız ışıklı külçe işlemen gerekir.

## Derleme

```bash
./gradlew build
```

Jar `build/libs/` altında oluşur. Oyunu denemek için `./gradlew runClient`, mekaniğin oyun içi
testleri için `./gradlew runGameTestServer`.
