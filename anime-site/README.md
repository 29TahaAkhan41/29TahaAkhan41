# AniTR: Türkçe Altyazılı Anime İzleme Sitesi

Saf HTML, CSS ve JavaScript ile yazılmış, sunucu gerektirmeyen bir anime izleme sitesi.

## Özellikler
- Anime kataloğu, arama (Türkçe karakter duyarlı) ve tür filtreleri
- Anime detay sayfası, bölüm listesi, "Listeme Ekle"
- **Türkçe altyazılı oynatıcı** (WebVTT): boyut, renk ve arka plan ayarı, ±0,5 sn senkron düzeltme
- Kaldığın yerden devam etme ve "İzlemeye Devam Et" bölümü (tarayıcıda saklanır)
- Klavye kısayolları: Boşluk, ←/→, J/L, F, M, C
- **Kendi Dosyanı İzle**: bilgisayarındaki video + `.srt`/`.vtt` altyazıyı seçip izle.
  SRT otomatik VTT'ye çevrilir, Windows-1254 kodlu Türkçe altyazılar bozulmadan okunur.

## Çalıştırma
Altyazı dosyalarının yüklenebilmesi için siteyi bir web sunucusundan açın
(doğrudan `file://` ile açınca tarayıcılar altyazıyı engeller):

```bash
cd anime-site && python3 -m http.server 8000
```

Sonra tarayıcıda `http://localhost:8000` adresini açın. GitHub Pages'te de ek ayar gerekmeden çalışır.

## Yeni anime ekleme
`data.js` dosyasındaki `CATALOG` listesine bir nesne ekleyin ve Türkçe altyazıyı `subs/` klasörüne
`.vtt` olarak koyun. Elinizdeki altyazı `.srt` ise başına `WEBVTT` satırını ekleyip zaman
damgalarındaki virgülü noktaya çevirmeniz yeterli (`00:01:02,500` → `00:01:02.500`).

## Telif hakkı
Yalnızca yayın hakkına sahip olduğunuz veya açık lisanslı içerikleri ekleyin. Demo içerikler
Blender Foundation'ın Creative Commons lisanslı filmleridir (Sintel, Tears of Steel,
Elephants Dream, Big Buck Bunny). Demo altyazıların zamanlamaları yaklaşıktır.
