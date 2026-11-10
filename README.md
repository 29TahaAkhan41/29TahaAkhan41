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

## Büyüler

Büyüler **Büyü Kitabı** okunarak öğrenilir (sağ tık; kitap harcanır, bilinen büyünün kitabı harcanmaz).
Öğrenilen büyüler ölünce kaybolmaz.

### Kitaplar nereden çıkar

Köylere (ova, çöl, savan, karlı, tayga) yeni bir **büyücü evi** eklenir: taş tuğladan, mor camlı,
sivri çatılı küçük bir kule; içinde kürsü, kitaplıklar, kazan ve bir sandık vardır.

- Bir köyde **en fazla bir** büyücü evi kurulur ve sandığından **tek bir** Büyü Kitabı çıkar
  (yanında kitap, kâğıt, ametist, lapis gibi ufak ganimetler). Kitaptaki büyü rastgeledir;
  düşük aşama büyüleri daha sık çıkar.
- Çoğu köyde çıkar ama her köyde olmayabilir. Köy yerleşimi evi birden fazla
  arsaya seçerse yalnızca ilki kurulur, diğer arsalar boş kalır.
- Yalnızca yeni oluşan köylerde çıkar; önceden keşfedilmiş köylere eklenmez.

### Büyü kullanmak

| Tuş (varsayılan) | İş |
|---|---|
| R | Seçili büyüyü yap |
| G | Sonraki büyüye geç |
| V / C | Büyü gücünü artır / azalt |

Tuşlar Seçenekler > Kontroller > Büyü Modu altından değiştirilebilir.

- Her büyünün bir **gereken aşaması** ve bir **taban mana bedeli** vardır. Aşaman yetmiyorsa büyüyü
  hiç kullanamazsın; taban bedelden az manayla da kullanamazsın.
- **Güç**: büyünün kendi aşamasında güç 1'dir; üstüne çıktığın her aşama için en fazla güç 1 artar.
  Mana bedeli = taban bedel × güç; büyünün etkisi güçle birlikte artar. Yani düşük bir büyüyü yüksek
  aşamada daha çok manayla çok daha güçlü kullanabilirsin, ama büyük bir büyüyü az manayla kullanamazsın.
- Seçili büyü, güç ve mana bedeli mana barının altında görünür.

Şu an oyunda yalnızca sistemi denemek için konmuş **iki geçici örnek büyü** vardır
(Mana Oku – Uyanmış, 2 mana; Mana Patlaması – Büyücü, 60 mana). Gerçek büyüler `spell/Spells.java`
içine eklenecek.

## Geliştirme

Gerekenler: **JDK 25** (Minecraft 26.3 bunu şart koşuyor). Gradle, wrapper ile kendiliğinden iner.

```bash
./gradlew runClient          # modla birlikte oyunu aç
./gradlew runServer          # sunucu aç
./gradlew runGameTestServer  # otomatik oyun içi testleri çalıştır
./gradlew build              # build/libs/spellmod-<sürüm>.jar üret ve indir/ klasörüne kopyala
```

Hazır `.jar` dosyası `indir/` klasöründedir; her `./gradlew build` onu günceller. Modda değişiklik
yapınca build alıp `indir/` klasörünü de commit et.

### Kod yapısı

```
src/main/java/com/tahaakhan/spellmod/
├── SpellMod.java        mod giriş noktası
├── mana/                mana kuralları, aşamalar, blok kırma olayı, /mana komutu
├── block/               mana masası ve işleme mantığı
├── menu/                mana masası arayüzünün sunucu tarafı
├── spell/               büyü tanımı, öğrenme ve kullanma kuralları
├── network/             tuş basışlarını sunucuya taşıyan paket
├── world/               köylerdeki büyücü evi ve köy başına tek kitap kuralı
├── item/                işlenmiş mana (özümseme)
├── registry/            eşya, attachment, yaratıcı sekme kayıtları
├── client/              mana barı (HUD), mana masası ekranı ve büyü tuşları
└── gametest/            otomatik testler
```
