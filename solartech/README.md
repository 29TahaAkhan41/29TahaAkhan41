# SolarTech

Horizon (Minecraft: Rust Edition) için teknik mod: güneş paneli, enerji kablosu ve
elektrikli fırın.

Sürüm 0.2.1. Horizon'un `4acdda5` (12 Kasım 2026) kaynağına sabitlenmiştir: başlatıcı 0.2.62,
Nightly `fdc87ae` kaynağıyla native mod derleyemiyor (ürettiği giriş dosyası o kaynakta olmayan
`horizon_threads::GameAllocator` türünü istiyor). Başlatıcı bu yüzden derlerken oyunu bu
kaynağa taşır.

## Bloklar

### Güneş Paneli

- Üstü açık gökyüzüne bakarken gündüz enerji üretir: öğlen, açık havada **20 FE/tick**.
- Üretim güneşin yüksekliğine göre değişir; yağmurda %40'a, fırtınada %10'a düşer, gece ve
  üstü kapalıyken sıfırdır.
- **100.000 FE** depolar. Güneş alırken üst yüzeyi parlak maviye döner.
- Sağ tıklayınca arayüzü açılır: depodaki enerji, doluluk çubuğu ve anlık üretim.

### Enerji Kablosu

- Yanındaki panele, fırına ve diğer kablolara kendiliğinden bağlanır.
- Enerjiyi panelden makineye taşır. Bağlantı başına en çok **400 FE/tick**, kablo başına
  2.000 FE tampon.

### Elektrikli Fırın

- Yakıt yerine enerjiyle çalışır: **20 FE/tick**, eşya başına 100 tick (normal fırının iki
  katı hız, eşya başına 2.000 FE). Öğlen tek panel bir fırını kesintisiz çalıştırır.
- **20.000 FE** depolar. Çalışırken önü yanar.
- Arayüzünde giriş ve çıkış yuvası, enerji çubuğu ve ilerleme çubuğu vardır.
- Huniler üstten ve yanlardan girişe eşya koyar, alttan çıkışı alır.
- Tarifleri kendi türündedir (`solartech:electric_smelting`): 57 yaygın eritme tarifi
  hazır gelir (cevherler, ham metaller, kum, taş, kil, kütükler, etler). Veri paketiyle
  yenisi eklenebilir:

  ```json
  { "type": "solartech:electric_smelting",
    "ingredient": "minecraft:raw_iron",
    "result": { "id": "minecraft:iron_ingot" } }
  ```

## Enerji sistemi

Enerji birimi FE'dir. Paneller üretir, kablolar taşır, makineler tüketir:

- Panel, yanındaki kabloya ve makineye enerji verir; enerji almaz.
- Kablo önce yanındaki makineleri besler, sonra komşu kablolarla dengelenir.
- Makine yalnızca alır.

Panel doğrudan fırının yanına da konabilir; kablo şart değildir. Enerji her blokta bir
tick bekler, yani uzun hatlarda uca birkaç tick gecikmeyle ulaşır.

## Tarifler (çalışma masası)

```
Güneş Paneli            Enerji Kablosu (6 adet)    Elektrikli Fırın
Cam    Cam      Cam     Bakır    Bakır    Bakır    Demir  Demir    Demir
Lapis  Kızıltaş Lapis   Kızıltaş Kızıltaş Kızıltaş Demir  Fırın    Demir
Demir  Bakır    Demir   Bakır    Bakır    Bakır    Bakır  Kızıltaş Bakır
```

## Kurulum

Mod iki dosyadan oluşur, ikisi de gerekli:

| Dosya | Ne | Nereye |
|---|---|---|
| `dist/solartech.hmod` | İçerik: bloklar, modeller, dokular, tarifler | `<oyun klasörü>/horizon-mods/` |
| `dist/solartech.hnmod` | Rust kodu: enerji, makineler, arayüzler | `<oyun klasörü>/horizon-native-mods/` |

Oyun klasörü, başlatıcıda **Oyna**'nın yanındaki klasör düğmesiyle açılır (`options.txt`
dosyasının olduğu yer). Klasörler yoksa oluştur.

1. İki dosyayı yukarıdaki klasörlere kopyala (eski sürümlerin üzerine yaz).
2. Başlatıcıda **Modlar** sayfasında SolarTech'i aç ve "Native build" satırından **Build**'e bas.
   Başlatıcı oyunu modla birlikte yeniden derler; ilk derleme Rust'ı indirir ve 20-30 dakika
   sürebilir, sonrakiler daha kısadır.
3. Oyunu başlat, Options > Mods'ta SolarTech'in açık olduğunu kontrol et ve yeniden başlat.

Native modlar korumalı alanda çalışmaz; başlatıcı bu yüzden derlemeden önce onay ister.
Kaynak kodun tamamı `native/api/src/` içindedir.

0.1.0'dan yükseltirken: panelin blok şablonu değişti, bu yüzden eski sürümle yerleştirilmiş
paneller kaybolabilir ya da boş görünebilir. Kırıp yeniden yerleştir.

## Kaynaktan paketleme

```bash
./build.sh
```

`dist/` altındaki iki dosyayı yeniden üretir. Dokular `python3 tools/make_textures.py`
(Pillow gerekir), fırın tarifleri `python3 tools/make_recipes.py` ile üretilir.

## Kod düzeni

| Dosya | İçerik |
|---|---|
| `native/api/src/lib.rs` | Horizon hook'ları: blok varlıkları, tick, kaplar |
| `native/api/src/grid.rs` | Enerji ağı: bloklar arası aktarım |
| `native/api/src/smelting.rs` | Fırının tarifleri ve eritme adımı |
| `native/api/src/screens.rs` | Panel ve fırın arayüzleri |

## Sınırlar

- Bu Horizon sürümü trait modlara komşu bloğun enerjisine yazma yardımcısı açmıyor. Mod bu
  yüzden kendi ağını tutar: enerji yalnızca SolarTech blokları arasında akar. Bloklar
  Horizon'un standart enerji tamponunu da bildirir, ama başka modlarla birlikte denenmedi.
- Panel tam bloktur: bu sürümün içerik biçimi ince, ışık geçiren blok tanımlamaya izin
  vermiyor.
- Elektrikli fırın vanilla eritme tablosunu okuyamaz (bu sürümde modlara açık değil);
  yalnızca kendi tarif türünü çalıştırır.
- Arayüz metinleri Türkçe ve sabittir.
- Bir blok kırıldığında ya da chunk'ı kapandığında o an yolda olan en fazla birkaç yüz FE
  kaybolabilir.

## Doğrulama durumu

- Enerji ağı, eritme adımı, üretim formülü ve arayüz hesapları 21 birim testiyle doğrulandı.
- Kod, kullanıcının makinesinde Horizon `fdc87ae` kaynağına karşı derlendi (`mod-solartech`
  adımı geçti); oyunun kendisi başlatıcı uyumsuzluğu yüzünden bağlanamadı. `4acdda5` ile
  derleme ve oyun içi davranış henüz denenmedi. Modun kullandığı hook imzaları iki kaynakta
  aynıdır.
