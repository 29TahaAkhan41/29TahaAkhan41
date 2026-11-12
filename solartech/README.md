# SolarTech

Horizon (Minecraft: Rust Edition) için teknik mod. Şimdilik tek içerik: **Güneş Paneli**.

Nightly `2026-11-08 · fdc87ae` için yazıldı.

## Güneş Paneli

- Üstü açık gökyüzüne bakarken gündüz enerji üretir: öğlen, açık havada **20 FE/tick**.
- Üretim güneşin yüksekliğine göre değişir; yağmurda %40'a, fırtınada %10'a düşer, gece ve
  üstü kapalıyken sıfırdır.
- **100.000 FE** depolar. Enerji üst yüz hariç her yüzden çekilebilir (tek seferde en çok 200 FE).
- Güneş alırken üst yüzeyi parlak maviye döner.
- Elinde **çubuk** (stick) ile panele sağ tıklayınca aksiyon çubuğunda dolu enerji ve anlık
  üretim görünür.

Tarif (çalışma masası):

```
Cam    Cam      Cam
Lapis  Kızıltaş Lapis
Demir  Bakır    Demir
```

## Kurulum

Mod iki dosyadan oluşur, ikisi de gerekli:

| Dosya | Ne | Nereye |
|---|---|---|
| `dist/solartech.hmod` | İçerik: blok, model, doku, tarif | `<oyun klasörü>/horizon-mods/` |
| `dist/solartech.hnmod` | Rust kodu: enerji üretimi | `<oyun klasörü>/horizon-native-mods/` |

Oyun klasörü, başlatıcıda **Oyna**'nın yanındaki klasör düğmesiyle açılır (`options.txt`
dosyasının olduğu yer). Klasörler yoksa oluştur.

1. İki dosyayı yukarıdaki klasörlere kopyala.
2. Başlatıcıda **Modlar** sayfasında SolarTech'i aç ve "Native build" satırından **Build**'e bas.
   Başlatıcı oyunu modla birlikte yeniden derler; ilk derleme Rust'ı indirir ve 20-30 dakika
   sürebilir.
3. Oyunu başlat, Options > Mods'ta SolarTech'in açık olduğunu kontrol et ve yeniden başlat.

Native modlar korumalı alanda çalışmaz; başlatıcı bu yüzden derlemeden önce onay ister.
Kaynak kodun tamamı `native/api/src/lib.rs` içindedir.

## Kaynaktan paketleme

```bash
./build.sh
```

`dist/` altındaki iki dosyayı yeniden üretir. Dokular `python3 tools/make_textures.py` ile
çizilir (Pillow gerekir).

## Sınırlar

- Bu Horizon sürümünde trait modlara açık enerji aktarma yardımcısı yok, bu yüzden panel
  enerjiyi komşu bloklara kendisi itmez; enerjiyi çeken taraf (kablo, makine) alır. Kablo ve
  makine henüz bu modda yok.
- Panel tam bloktur: bu sürümün içerik biçimi ince, ışık geçiren blok tanımlamaya izin
  vermiyor.

## Doğrulama durumu

- Üretim formülü ve NBT okuma birim testleriyle doğrulandı (`native/api/src/lib.rs`).
- Kod, Horizon `fdc87ae` kaynağından okunan imzalarla elle yazılmış bir API taklidine karşı
  derlendi. Gerçek oyuna karşı derlenmedi ve oyun içinde denenmedi.
