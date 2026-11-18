# 🎮 Oyun Çevirmeni

Oyunlardaki **her şeyi**, yani menüleri, butonları, diyalogları, görev yazılarını ve arayüzü Türkçeye çeviren bir masaüstü uygulaması.

İki şekilde çalışır:

| Mod | Ne yapar? | Hangi oyunlarda? |
|---|---|---|
| **🎮 Canlı Ekran Çevirisi** | Ekrandaki yazıları okur (OCR) ve her yazının tam üstüne Türkçesini, oyunun kendi renginde yazar. | **Her oyunda** (dosyalarına erişilemeyen oyunlar dahil) |
| **📁 Dil Dosyası Çevirisi** | Oyunun dil dosyalarını kalıcı olarak Türkçeye çevirir. `%s`, `{0}`, `§a`, `<b>` gibi kodlar bozulmaz. | Minecraft modları, Unity ve RPG Maker JSON'ları, Paradox (.yml), .po, .csv, .xml, .ini, .lang… |

---

## Kurulum (Windows, en kolay yol: hazır .exe)

1. <https://github.com/29TahaAkhan41/29TahaAkhan41/releases/tag/oyun-cevirmen> sayfasından
   **OyunCevirmeni-Windows.zip** dosyasını indirin.
2. Zip'e sağ tıklayıp **Tümünü ayıkla** deyin (zip'in içinden doğrudan çalıştırmayın).
3. Klasördeki **OyunCevirmeni.exe**'ye çift tıklayın. Kurulum gerekmez: Tesseract OCR ve
   11 dilin paketi (İngilizce, Japonca, Çince, Korece, Rusça, Almanca, Fransızca, İspanyolca,
   İtalyanca, Portekizce, Lehçe) içinde gelir.

> Windows "Windows kişisel bilgisayarınızı korudu" uyarısı gösterirse **Ek bilgi → Yine de çalıştır**
> deyin. Uygulama imzalı olmadığı için bu uyarı normaldir.
> .exe sürümünde isteğe bağlı EasyOCR ve Argos yoktur; diğer her şey (yapay zekâ motorları dahil) vardır.
> Hata olursa ayrıntılar `%USERPROFILE%\.oyun_cevirmen\hata.log` dosyasına yazılır.

## Kurulum (Windows, Python ile)

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
```bash
python -m oyun_cevirmen dosya en_us.json --motor gemini --anahtar ANAHTARINIZ
```

---

## Çeviri motorları

| Motor | Artı | Eksi |
|---|---|---|
| **Google Çeviri** (varsayılan) | Ücretsiz, anahtar gerekmez | İnternet gerekir; çok hızlı isteklerde kısa süre engelleyebilir |
| **🤖 Yapay zekâ: Google Gemini** | Bağlamı anlar, oyun terimlerini doğru çevirir. Ücretsiz katmanı var. | Ücretsiz API anahtarı gerekir; dakikalık istek sınırı var |
| **🤖 Yapay zekâ: Groq** | Ücretsiz katmanı var, çok hızlı | Ücretsiz API anahtarı gerekir; günlük/dakikalık sınır var |
| **🤖 Yapay zekâ: Ollama** | Tamamen ücretsiz, **internetsiz**, sınırsız; yazılar bilgisayardan çıkmaz | İyi bir bilgisayar ister (8 GB+ RAM, tercihen ekran kartı); ilk kurulum birkaç GB |
| **DeepL** | Çok doğal Türkçe | Ücretsiz API anahtarı gerekir: <https://www.deepl.com/pro-api> (ayda 500.000 karakter ücretsiz) |
| **Argos** | Tamamen çevrimdışı, hafif | Kalitesi daha düşük |

### 🤖 Yapay zekâ motorlarını kurma

Yapay zekâ, klasik çeviriden farklı olarak yazının **oyun yazısı olduğunu bilerek** çevirir.
Kısa menü yazılarını doğru yorumlar ("Load" → "Yükle"), terimleri oyuncuların kullandığı
biçimde çevirir ve karakter/yer adlarını olduğu gibi bırakır.

**Google Gemini (önerilen)**
1. <https://aistudio.google.com/apikey> adresine Google hesabınızla girin.
2. **Create API key** ile anahtar oluşturun ve kopyalayın.
3. Oyun Çevirmeni'nde motoru *Yapay zekâ: Google Gemini* yapıp anahtarı **API anahtarı** kutusuna yapıştırın.

**Groq**
1. <https://console.groq.com/keys> adresinde ücretsiz hesap açın, **Create API Key** ile anahtar alın.
2. Motoru *Yapay zekâ: Groq* yapıp anahtarı yapıştırın.

**Ollama (internetsiz)**
1. <https://ollama.com/download> adresinden Ollama'yı kurun ve açın.
2. Komut istemine (cmd) şunu yazıp modeli indirin (yaklaşık 6,6 GB):
   ```bash
   ollama pull qwen3.5:9b
   ```
3. Motoru *Yapay zekâ: Ollama* yapın. Anahtar gerekmez.
   Bilgisayarınız zayıfsa daha küçük bir model indirip **Model** kutusuna adını yazın (ör. `qwen3.5:4b`).
   Güçlü bir ekran kartınız varsa daha büyük bir model daha iyi çevirir. Örneğin
   `ollama pull qwen3.8:27b` ile indirip **Model** kutusuna `qwen3.8:27b` yazabilirsiniz
   (yaklaşık 18 GB; rahat çalışması için 24 GB ekran kartı belleği önerilir).
   Düşünen (thinking) modellerde düşünme çeviri sırasında otomatik kapatılır, böylece daha hızlı cevap verirler.

**Model** kutusu boş bırakılırsa varsayılan model kullanılır (Gemini: `gemini-2.5-flash`,
Groq: `llama-3.3-70b-versatile`, Ollama: `qwen3.5:9b`). Servisler modellerini zamanla
değiştirebilir. "Model bulunamadı" hatası alırsanız servisin sitesindeki güncel model adını
bu kutuya yazın.

> Ücretsiz katmanların sınırlarını ve koşullarını servisler belirler ve zamanla değiştirebilir.
> Gemini'nin ücretsiz katmanında gönderilen yazılar Google tarafından ürün geliştirmek için
> kullanılabilir. Bunu istemiyorsanız Ollama'yı seçin.

Ayarlar ve önbellek `%USERPROFILE%\.oyun_cevirmen\` klasöründe tutulur.

---

## Sorun giderme

| Sorun | Çözüm |
|---|---|
| "Tesseract bulunamadı" | *Tesseract yolu* alanına `C:\Program Files\Tesseract-OCR\tesseract.exe` yazın |
| Çeviri oyunun üstünde görünmüyor | Oyunu kenarlıksız pencere moduna alın |
| Kutular yazıdan kayık | Windows ekran ölçeklendirmesini değiştirdiyseniz uygulamayı yeniden başlatın |
| Bazı yazılar okunmuyor | *Alan seç* ile bölgeyi daraltın veya EasyOCR'a geçin |
| "Çok fazla istek" / "kullanım sınırı" hatası | Otomatik yenileme süresini 3-5 sn yapın, biraz bekleyin veya başka motor seçin |
| "Ollama'ya bağlanılamadı" | Ollama uygulamasının açık olduğundan emin olun |
| "Model bulunamadı" | Model adını kontrol edin; Ollama'da `ollama pull <model>` ile indirin |
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
