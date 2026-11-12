# PyLauncher

Saf Python ile yazılmış bir **Minecraft: Java Edition launcher'ı**. Ek paket gerektirmez
(yalnızca Python 3.9+ standart kütüphanesi). Oyunun kendisi Mojang'ın resmi sunucularından
indirilir; bu depo oyun dosyası içermez.

## Özellikler

- Tüm sürümler: release, snapshot, eski beta/alpha
- İstemci, kütüphane, native ve asset indirme (paralel, SHA-1 doğrulamalı, kaldığı yerden devam)
- Doğru Java'yı otomatik bulur; yoksa Mojang'ın resmi Java çalışma ortamını indirir
- Fabric mod yükleyicisi (`--fabric`)
- Microsoft hesabıyla giriş (cihaz kodu akışı, parola launcher'a girilmez)
- Komut satırı ve Tkinter grafik arayüzü

## Kullanım

`launcher/` dizininde:

```bash
python -m pylauncher gui                      # grafik arayüz
python -m pylauncher versions                 # sürümleri listele
python -m pylauncher login                    # Microsoft ile giriş
python -m pylauncher launch 1.21.1            # kur ve başlat
python -m pylauncher launch 1.21.1 --fabric   # Fabric ile
python -m pylauncher launch latest --memory 4096 --resolution 1280 720
python -m pylauncher install 1.20.1           # yalnızca indir
```

Veriler `~/.pylauncher` altında tutulur (Windows: `%APPDATA%\PyLauncher`,
macOS: `~/Library/Application Support/PyLauncher`). `--root` ya da `PYLAUNCHER_HOME` ile
değiştirilebilir. Dünyalar ve modlar `game/` klasöründedir (`game/mods`).

Linux'ta grafik arayüz için `python3-tk` paketi gerekir.

## Microsoft girişi

Oynamak için Minecraft: Java Edition'a sahip bir Microsoft hesabı gerekir. Microsoft,
her launcher'ın kendi uygulama kimliğini (client ID) kullanmasını ister:

1. <https://portal.azure.com> → **App registrations** → **New registration**.
   Hesap türü: *Personal Microsoft accounts only*.
2. **Authentication** → *Allow public client flows* → **Yes**.
3. Yeni uygulamaların Minecraft API'sine erişmesi için Mojang'ın onayı gerekir:
   <https://aka.ms/mce-reviewappid> formunu doldurun. Onay gelmeden giriş
   `login_with_xbox` adımında 403 hatası verir.
4. Kimliği kaydedin:

```bash
python -m pylauncher config client_id <UYGULAMA-KİMLİĞİ>
```

`--offline` (arayüzde "Çevrimdışı") yalnızca daha önce giriş yapılmış bir hesapla çalışır;
internet yokken tek oyunculu oynamak içindir.

Token'lar `accounts.json` içinde, yalnızca kullanıcının okuyabileceği izinlerle saklanır.

## Testler

```bash
python -m unittest discover -s tests
```

## Kapsam dışı (şimdilik)

Forge/NeoForge/Quilt kurulumu, mod indirme, birden fazla profil (instance), skin yönetimi.

Minecraft, Mojang AB'nin ticari markasıdır. Bu proje Mojang ya da Microsoft ile bağlantılı değildir.
