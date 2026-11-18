# 🎮 Oyun Çevirmeni

Oyunlardaki **her şeyi**, yani menüleri, butonları, diyalogları, görev yazılarını ve arayüzü Türkçeye çeviren bir masaüstü uygulaması.

İki şekilde çalışır:

| Mod | Ne yapar? | Hangi oyunlarda? |
|---|---|---|
| **🎮 Canlı Ekran Çevirisi** | Ekrandaki yazıları okur (OCR) ve her yazının tam üstüne Türkçesini, oyunun kendi renginde yazar. | **Her oyunda** (dosyalarına erişilemeyen oyunlar dahil) |
| **📁 Dil Dosyası Çevirisi** | Oyunun dil dosyalarını kalıcı olarak Türkçeye çevirir. `%s`, `{0}`, `§a`, `<b>` gibi kodlar bozulmaz. | Minecraft modları, Unity ve RPG Maker JSON'ları, Paradox (.yml), .po, .csv, .xml, .ini, .lang… |

---

## Kurulum (Windows)

1. **Python 3.10 veya üstünü** kurun: <https://www.python.org/downloads/>
   Kurulumda **"Add Python to PATH"** kutusunu işaretleyin.
2. **Tesseract OCR** kurun (ekrandaki yazıları okumak için):
   <https://github.com/UB-Mannheim/tesseract/wiki> sayfasından Windows kurulum dosyasını indirin.
   Kurulumda *Additional language data* altından oyunun dilini seçin (İngilizce zaten var; Japonca, Rusça vb. için işaretleyin).
3. Bu klasördeki **`baslat.bat`** dosyasına çift tıklayın.
   İlk açılışta gerekli paketler otomatik kurulur (1-2 dakika sürer).

> Linux/macOS: `./baslat.sh` (Tesseract için: `sudo apt install tesseract-ocr` / `brew install tesseract`)

İsteğe bağlı ekler:
```bash
pip install -r requirements-extra.txt
```
- **EasyOCR**: stilize/oyun fontlarını daha iyi okur (NVIDIA ekran kartı varsa hızlıdır)
- **Argos**: internet olmadan çeviri

---

## 🎮 Canlı Ekran Çevirisi: Kullanım

1. Oyunu **Pencereli** ya da **Kenarlıksız pencere (Borderless)** modunda açın.
   *Özel tam ekran* modunda Windows, çeviri katmanının oyunun üstünde görünmesine izin vermeyebilir.
2. Oyun Çevirmeni'nde oyunun dilini seçin (ör. İngilizce).
3. Oyundayken kısayolları kullanın:

| Tuş | İşlev |
|---|---|
| **F9** | Ekrandaki yazıları şimdi çevir |
| **F10** | Çeviriyi göster/gizle (orijinali görmek için) |
| **F11** | Otomatik mod: ekran değiştikçe kendiliğinden yeniden çevirir |

Kısayollar arayüzden değiştirilebilir (ör. `ctrl+shift+t`).

**İpuçları**
- **Alan seç…** ile yalnızca diyalog kutusu veya altyazı bölgesini seçerseniz çeviri daha hızlı ve daha doğru olur.
- Çeviri kutuları tıklamayı engellemez; tıklamalar oyuna geçer (Windows).
- Aynı yazı ikinci kez görüldüğünde önbellekten anında gelir.
- Fontlar çok süslüyse OCR motorunu **EasyOCR** yapın.

---

## 📁 Dil Dosyası Çevirisi: Kullanım

1. **Dosya…** ile dil dosyasını (ör. `assets/modadi/lang/en_us.json`) ya da **Klasör…** ile bütün bir dil klasörünü seçin.
2. Çıktı adı otomatik önerilir: `en_us.json → tr_tr.json`, `l_english.yml → l_turkish.yml`, diğerleri `ad_tr.uzantı`.
3. **Türkçeye çevir**'e basın. Orijinal dosyalar değiştirilmez.

Korunanlar: `%s %d %1$s`, `{0} {player} {{count}}`, Minecraft `§a &b` renk kodları, `<b> <color=#fff>`, `[b] [color=red]`, `$VAR$`, `\n`, dosya yolları, `minecraft:stone` gibi kimlikler ve sayılar.

### Komut satırından
```bash
python -m oyun_cevirmen dosya en_us.json
```
```bash
python -m oyun_cevirmen dosya Localization/ -o Localization_tr --kaynak en --motor google
```

---

## Çeviri motorları

| Motor | Artı | Eksi |
|---|---|---|
| **Google Çeviri** (varsayılan) | Ücretsiz, anahtar gerekmez | İnternet gerekir; çok hızlı isteklerde kısa süre engelleyebilir |
| **DeepL** | En doğal Türkçe | Ücretsiz API anahtarı gerekir: <https://www.deepl.com/pro-api> (ayda 500.000 karakter ücretsiz) |
| **Argos** | Tamamen çevrimdışı | Kalitesi daha düşük |

Ayarlar ve önbellek `%USERPROFILE%\.oyun_cevirmen\` klasöründe tutulur.

---

## Sorun giderme

| Sorun | Çözüm |
|---|---|
| "Tesseract bulunamadı" | *Tesseract yolu* alanına `C:\Program Files\Tesseract-OCR\tesseract.exe` yazın |
| Çeviri oyunun üstünde görünmüyor | Oyunu kenarlıksız pencere moduna alın |
| Kutular yazıdan kayık | Windows ekran ölçeklendirmesini değiştirdiyseniz uygulamayı yeniden başlatın |
| Bazı yazılar okunmuyor | *Alan seç* ile bölgeyi daraltın veya EasyOCR'a geçin |
| "Çok fazla istek" hatası | Otomatik yenileme süresini 3-5 sn yapın veya DeepL kullanın |
| Kısayollar oyunda çalışmıyor | Oyun yönetici olarak çalışıyorsa Oyun Çevirmeni'ni de **yönetici olarak** açın |

> Not: Bu uygulama oyun dosyalarına veya belleğine müdahale etmez; yalnızca ekran görüntüsünü okur. Bu yüzden hile koruması olan oyunlarda genellikle sorun çıkarmaz, ama bunun garantisi yoktur.
> Dil dosyası çevirisini kendi kullanımınız için yapın. Çevrilmiş dosyaları paylaşmadan önce oyunun/modun lisansına bakın.

## Geliştirme

```bash
pip install pytest
```
```bash
python -m pytest tests
```
