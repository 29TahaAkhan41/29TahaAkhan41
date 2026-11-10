# Spell Mod (Büyü Modu)

Minecraft **26.3** için **NeoForge** ile yazılmış bir büyü modu. Oyuncu manaya hazır sahip olmaz;
onu bulması, işlemesi, özümsemesi ve vücudunu ona alıştırması gerekir.

## Mana sistemi

1. **Ham mana bulmak** – Hayatta kalma modunda kırılan bloklardan düşük bir ihtimalle
   **İşlenmemiş Mana** düşer. Başlangıçta şans %0,2'dir. Her buluş (+1) ve her özümseme (+2)
   **mana tecrübesi** kazandırır; her tecrübe puanı şansı %0,04 artırır (en fazla %5).
   Anında kırılan bloklar (çimen, çiçek, meşale...) mana vermez.
2. **İşlemek** – İşlenmemiş mana tek başına işe yaramaz; bir masada **İşlenmiş Mana**'ya
   dönüştürülmesi gerekir. *Masa henüz yapılmadı*; o yüzden İşlenmiş Mana şimdilik yalnızca
   yaratıcı moddan veya `/give` ile alınabilir.
3. **Özümsemek** – İşlenmiş Mana sağ tıkla özümsenir. Her özümseme 10 mana verir ve vücudun
   **mana kapasitesini** 2 artırır (en fazla 200).
4. **Alışmak** – Kapasiteye sığmayan mana boşa gider ve **zarar verir** (büyü hasarı; ağır
   olursa Mide Bulantısı ve Zayıflık). Kapasite büyüdükçe aynı taşma daha az acıtır.
   Yeni oyuncunun kapasitesi 0 olduğu için ilk özümsemeler can yakar.

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
mananı, tecrübeni ve ham mana bulma şansını gösterir. Mana verileri ölünce kaybolmaz.

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
├── item/                işlenmiş mana (özümseme)
├── registry/            eşya, attachment, yaratıcı sekme kayıtları
├── client/              mana barı (HUD)
└── gametest/            otomatik testler
```
