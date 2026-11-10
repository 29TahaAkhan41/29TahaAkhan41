# Spell Mod (Büyü Modu)

Minecraft **26.3** için **NeoForge** ile yazılmış, mana tabanlı bir büyü modu.

## Özellikler

- **Sihirli Asa** – sağ tık ile seçili büyüyü yapar, eğilerek (Shift) sağ tık ile büyü değiştirir.
- **Mana** – her oyuncunun 100 manası vardır; saniyede 4 mana yenilenir, dünyayla birlikte kaydedilir.
  Asa elindeyken ekranın sol üstünde mana barı ve seçili büyü görünür.
- **Mana Kristali** – sağ tık ile kullanılır, anında 50 mana yeniler.

| Büyü        | Mana | Bekleme | Etki                                                        |
|-------------|------|---------|-------------------------------------------------------------|
| Ateş Topu   | 20   | 0,75 sn | Baktığın yöne bir ateş topu fırlatır                        |
| İyileştirme | 30   | 2 sn    | 4 kalp iyileştirir + 5 sn Yenilenme                         |
| Işınlanma   | 25   | 1,5 sn  | Baktığın yere (en fazla 16 blok) ışınlar                    |
| Yıldırım    | 40   | 3 sn    | Baktığın bloğa/canlıya (en fazla 48 blok) yıldırım düşürür  |

Yaratıcı modda büyüler mana harcamaz.

## Tarifler

- **Sihirli Asa** (çalışma masası, çapraz): ametist parçası (sağ üst), elmas (orta), çubuk (sol alt)
- **Mana Kristali ×2** (şekilsiz): ametist parçası + lapis lazuli + ışıktaşı tozu

## Geliştirme

Gerekenler: **JDK 25** (Minecraft 26.3 bunu şart koşuyor). Gradle, wrapper ile kendiliğinden iner.

```bash
./gradlew runClient          # modla birlikte oyunu aç
./gradlew runServer          # sunucu aç
./gradlew runGameTestServer  # otomatik oyun içi testleri çalıştır
./gradlew build              # build/libs/spellmod-<sürüm>.jar üret
```

### Yeni büyü eklemek

1. `spell/SpellEffects.java` içine büyünün etkisini yazan bir metot ekle
   (`false` dönerse büyü başarısız sayılır ve mana harcanmaz).
2. `spell/Spell.java` içindeki enum'a mana bedeli ve bekleme süresiyle yeni bir satır ekle.
3. `assets/spellmod/lang/en_us.json` ve `tr_tr.json` dosyalarına `spell.spellmod.<isim>` çevirisini ekle.

### Kod yapısı

```
src/main/java/com/tahaakhan/spellmod/
├── SpellMod.java        mod giriş noktası
├── spell/               büyüler ve etkileri
├── mana/                mana mantığı ve yenilenme
├── item/                asa ve mana kristali
├── registry/            eşya, veri bileşeni, attachment, yaratıcı sekme kayıtları
├── client/              mana barı (HUD)
└── gametest/            otomatik testler
```
