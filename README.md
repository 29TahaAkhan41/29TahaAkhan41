# Spell Mod (Büyü Modu)

Minecraft **26.3** için **NeoForge** ile yazılmış bir büyü modu. Oyuncu manaya hazır sahip olmaz;
onu bulması, işlemesi, özümsemesi ve vücudunu ona alıştırması gerekir.

## Mana sistemi

1. **Ham mana bulmak** – Hayatta kalma modunda kırılan bloklardan düşük bir ihtimalle
   **İşlenmemiş Mana** düşer. Başlangıçta şans %0,2'dir. Her buluş (+1) ve her özümseme (+2)
   **mana tecrübesi** kazandırır; her tecrübe puanı şansı %0,04 artırır (en fazla %5).
   Anında kırılan bloklar (çimen, çiçek, meşale...) mana vermez.
2. **İşlemek** – İşlenmemiş mana tek başına işe yaramaz; **Mana Masası**'nda **İşlenmiş Mana**'ya
   dönüştürülmesi gerekir (aşağıya bak).
3. **Özümsemek** – İşlenmiş Mana sağ tıkla özümsenir. Her özümseme 10 mana verir ve vücudun
   **mana kapasitesini** 2 artırır (en fazla 200).
4. **Alışmak** – Kapasiteye sığmayan mana boşa gider ve **zarar verir** (büyü hasarı; ağır
   olursa Mide Bulantısı ve Zayıflık). Kapasite büyüdükçe aynı taşma daha az acıtır.
   Yeni oyuncunun kapasitesi 0 olduğu için ilk özümsemeler can yakar.

### Tarifler (çalışma masası)

**Mana Kapsülü** – ortada işlenmemiş mana, köşelerde cam, kenarlarda ender gözü:

```
Cam        Ender Gözü   Cam
Ender Gözü Ham Mana     Ender Gözü
Cam        Ender Gözü   Cam
```

**Mana Masası** – ortada mana kapsülü, altta 3 obsidyen, üstte ortada cam ve yanlarında ender gözü:

```
Ender Gözü Cam          Ender Gözü
(boş)      Mana Kapsülü (boş)
Obsidyen   Obsidyen     Obsidyen
```

Mana Masası ışık saçar (seviye 12), üstündeki mana girdabı ve yanlarındaki cam şerit hareketlidir,
kazmayla kırılır, kendisini ve içindekileri düşürür.

### Mana Masası'nda işleme

Masaya sağ tıklayınca mavi arayüz açılır: solda üstte **ham mana**, altta **yakıt (ender gözü)**,
sağda **çıkış** yuvası; ortada süre, kayıp riski, ilerleme çubuğu ve **İşle** butonu vardır.

- **İşle** butonuna basınca masa yuvadaki ham manaları tek tek işler; her parça **1 ender gözü** harcar.
  Ham mana, yakıt veya çıkışta yer bitince durur. Parça işlenmeye başladıktan sonra geri alınamaz.
- **Süre**, butona basan oyuncunun o güne kadar işlediği ham mana sayısına bağlıdır: ilk parça
  **10 dakika** sürer, işlenen her parça bir sonrakini %10 hızlandırır ve süre en az **1 saniyeye**
  kadar iner (yaklaşık 60 parça sonra).
- **Kayıp riski**: parça bitince mana yok olabilir (ender gözü de gider). Risk, oyuncunun
  **mana yatkınlığına** bağlıdır: yatkınlık %0 iken risk **%75**, %100 iken **%5**.
- **Mana yatkınlığı** = (mana tecrübesi × 0,5 + mana kapasitesi × 0,25), en fazla %100.
  Yani hem manayı tanıdıkça (bulmak, işlemek, özümsemek) hem de vücut alıştıkça artar.
- Her işlenen parça +1 mana tecrübesi kazandırır.
- Huni desteği: üstten ham mana, yanlardan ender gözü girer; alttan işlenmiş mana çıkar.
- Oyuncu oyundan çıkarsa masa, o oyuncunun son parçasındaki süre ve riskle devam eder.

### Aşamalar

| Aşama      | Gereken kapasite |
|------------|------------------|
| Uyanmamış  | 0                |
| Uyanmış    | 1                |
| Çırak      | 20               |
| Usta       | 50               |
| Büyücü     | 100              |
| Başbüyücü  | 200              |

Uyandıktan sonra ekranın sol üstünde aşama ve mana barı görünür. `/mana` komutu aşamanı,
mananı, tecrübeni, ham mana bulma şansını, yatkınlığını, işleme süreni ve kayıp riskini gösterir. Mana verileri ölünce kaybolmaz.

Bütün sayılar `mana/Mana.java` ve `mana/ManaStage.java` içinde sabit olarak durur.

## Geliştirme

Gerekenler: **JDK 25** (Minecraft 26.3 bunu şart koşuyor). Gradle, wrapper ile kendiliğinden iner.

```bash
./gradlew runClient          # modla birlikte oyunu aç
./gradlew runServer          # sunucu aç
./gradlew runGameTestServer  # otomatik oyun içi testleri çalıştır
./gradlew build              # build/libs/spellmod-<sürüm>.jar üret
```

### Kod yapısı

```
src/main/java/com/tahaakhan/spellmod/
├── SpellMod.java        mod giriş noktası
├── mana/                mana kuralları, aşamalar, blok kırma olayı, /mana komutu
├── block/               mana masası ve işleme mantığı
├── menu/                mana masası arayüzünün sunucu tarafı
├── item/                işlenmiş mana (özümseme)
├── registry/            eşya, attachment, yaratıcı sekme kayıtları
├── client/              mana barı (HUD) ve mana masası ekranı
└── gametest/            otomatik testler
```
