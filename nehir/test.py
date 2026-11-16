#!/usr/bin/env python3
"""ornekler/ ve ornekler/hatalar/ altındaki her .nehir dosyasını derler, çalıştırır
ve çıktısını (hata mesajları dahil) yanındaki .beklenen dosyasıyla karşılaştırır. Aynı adlı bir .girdi dosyası varsa
programa standart girdi olarak verilir.

Ardından Nehir ile yazılmış derleyici aşamalarını (kendi/ altındaki sözcükleyici,
ayrıştırıcı ve kod üretici) derler ve bütün .nehir dosyalarında Python'daki karşılıklarıyla aynı
çıktıyı verdiklerini sınar. En son, Nehir ile yazılmış derleyicinin kendini derleyip sabit
noktaya ulaştığını sınar.

  python3 test.py              sınamaları çalıştır
  python3 test.py --güncelle   .beklenen dosyalarını şimdiki çıktıyla yeniden yaz
"""
import glob
import os
import time
import subprocess
import sys
import tempfile

KÖK = os.path.dirname(os.path.abspath(__file__))


def ana():
    güncelle = any(a in ("--güncelle", "--guncelle", "--update") for a in sys.argv[1:])
    başarısız = 0
    with tempfile.TemporaryDirectory() as geçici:
        kaynaklar = sorted(glob.glob(os.path.join(KÖK, "ornekler", "*.nehir"))) + \
            sorted(glob.glob(os.path.join(KÖK, "ornekler", "hatalar", "*.nehir")))
        for kaynak in kaynaklar:
            # Hata mesajları dosya yolunu içerdiği için derleyici hep aynı
            # dizinden, göreli yolla çalıştırılır.
            göreli = os.path.relpath(kaynak, KÖK).replace(os.sep, "/")
            ad = os.path.splitext(göreli)[0].replace("ornekler/", "", 1)
            beklenen_yolu = os.path.splitext(kaynak)[0] + ".beklenen"
            try:
                with open(os.path.splitext(kaynak)[0] + ".girdi", encoding="utf-8") as f:
                    girdi = f.read()
            except FileNotFoundError:
                girdi = ""
            sonuç = subprocess.run(
                [sys.executable, "nehir.py", göreli,
                 "-o", os.path.join(geçici, os.path.basename(ad)), "--run"],
                cwd=KÖK, input=girdi, capture_output=True, text=True, encoding="utf-8")
            çıktı = sonuç.stdout + sonuç.stderr
            if güncelle:
                with open(beklenen_yolu, "w", encoding="utf-8") as f:
                    f.write(çıktı)
                print(f"yazıldı   {ad}")
                continue
            try:
                with open(beklenen_yolu, encoding="utf-8") as f:
                    beklenen = f.read()
            except FileNotFoundError:
                beklenen = None
            if çıktı == beklenen:
                print(f"geçti     {ad}")
            else:
                başarısız += 1
                print(f"BAŞARISIZ {ad}")
                print("  beklenen:", repr(beklenen))
                print("  çıkan:   ", repr(çıktı))
        if not güncelle:
            başarısız += kendi_derleyiciyi_sına(geçici, kaynaklar)
    return 1 if başarısız else 0


def kendi_derleyiciyi_sına(geçici, kaynaklar):
    """Nehir ile yazılmış aşamalar, her dosyada Python'daki karşılıklarıyla aynı çıktıyı,
    aynı hata mesajlarını (kaynak satırı, ipucu ve notlarıyla) ve aynı çıkış kodunu vermelidir."""
    def çalıştır(komut):
        s = subprocess.run(komut, cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        return s.returncode, s.stdout, s.stderr

    kaynaklar = list(kaynaklar)
    for kalıp in ("ornekler/moduller/*.nehir", "ornekler/hatalar/moduller/*.nehir",
                  "kendi/*.nehir", "kendi/sinamalar/*.nehir"):
        kaynaklar += sorted(glob.glob(os.path.join(KÖK, *kalıp.split("/"))))

    başarısız = 0
    for aşama, program, seçenek in (("sözcükleyici", "kendi/sozcuk_dok.nehir", "--sözcükler"),
                                   ("ayrıştırıcı", "kendi/agac_dok.nehir", "--ağaç")):
        ikili = os.path.join(geçici, os.path.splitext(os.path.basename(program))[0])
        kod, _, hata = çalıştır([sys.executable, "nehir.py", program, "-o", ikili])
        if kod != 0:
            başarısız += 1
            print(f"BAŞARISIZ {program} derlenemedi:", hata)
            continue
        farklı = 0
        for kaynak in kaynaklar:
            göreli = os.path.relpath(kaynak, KÖK).replace(os.sep, "/")
            beklenen = çalıştır([sys.executable, "nehir.py", göreli, seçenek])
            çıkan = çalıştır([ikili, göreli])
            if çıkan != beklenen:
                farklı += 1
                print(f"BAŞARISIZ kendi {aşama}: {göreli}")
                for b, ç in zip(beklenen, çıkan):
                    if b != ç:
                        print("  beklenen:", repr(b)[:300])
                        print("  çıkan:   ", repr(ç)[:300])
                        break
        if not farklı:
            print(f"geçti     kendi {aşama} ({len(kaynaklar)} dosyada Python ile aynı çıktı)")
        başarısız += farklı
    return (başarısız + kendi_kod_üreticiyi_sına(geçici, kaynaklar) + kendini_derlemeyi_sına(geçici)
            + renkleri_sına(geçici) + tuşları_sına(geçici) + windowsu_sına(geçici))


def windows_araçları():
    """Linux'ta Windows programı üretip çalıştırmak için MinGW-w64 ve Wine; yoksa None."""
    import shutil
    gcc = shutil.which("x86_64-w64-mingw32-gcc")
    wine = shutil.which("wine64") or ("/usr/lib/wine/wine64" if os.path.exists("/usr/lib/wine/wine64") else None)
    return (gcc, wine) if gcc and wine else None


def windowsu_sına(geçici):
    """Windows hedefi: örnekler Windows için derlenip Wine'da çalıştırılır ve çıktıları Linux'takilerle
    (.beklenen) karşılaştırılır; Windows için derlenmiş Nehir derleyicisi Wine'da kendini derleyip
    sabit noktaya ulaşmalıdır. MinGW-w64 ya da Wine yoksa atlanır."""
    araçlar = windows_araçları()
    if sys.platform == "win32" or araçlar is None:
        print("atlandı   windows (x86_64-w64-mingw32-gcc ve wine64 gerekir)")
        return 0
    gcc, wine = araçlar
    from concurrent.futures import ThreadPoolExecutor
    ortam = dict(os.environ, WINEDEBUG="-all", LANG="C.UTF-8", LC_ALL="C.UTF-8",
                 WINEPREFIX=os.path.join(geçici, "wine"))
    subprocess.run([wine, "cmd", "/c", "exit"], env=ortam, capture_output=True)    # Wine ortamını hazırla
    dizin = os.path.join(geçici, "windows")
    os.makedirs(dizin, exist_ok=True)

    def örnek(kaynak):
        göreli = os.path.relpath(kaynak, KÖK).replace(os.sep, "/")
        exe = os.path.join(dizin, göreli.replace("/", "_")[:-6] + ".exe")
        d = subprocess.run([sys.executable, "nehir.py", göreli, "--hedef", "windows", "-o", exe],
                           cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        p_çıktı, p_hata = "", ""
        if d.returncode == 0:
            girdi_yolu = os.path.splitext(kaynak)[0] + ".girdi"
            with open(girdi_yolu, "rb") if os.path.exists(girdi_yolu) else open(os.devnull, "rb") as girdi:
                p = subprocess.run([wine, exe], cwd=KÖK, stdin=girdi, capture_output=True, env=ortam, timeout=120)
            p_çıktı, p_hata = p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
        # .beklenen, nehir.py --run'ın çıktısıdır: önce standart çıktı, sonra standart hata.
        çıkan = d.stdout + p_çıktı + d.stderr + p_hata
        with open(os.path.splitext(kaynak)[0] + ".beklenen", encoding="utf-8") as f:
            beklenen = f.read()
        return göreli, çıkan == beklenen, beklenen, çıkan

    kaynaklar = sorted(glob.glob(os.path.join(KÖK, "ornekler", "*.nehir"))) + \
        sorted(glob.glob(os.path.join(KÖK, "ornekler", "hatalar", "*.nehir")))
    başarısız = 0
    with ThreadPoolExecutor(max_workers=8) as havuz:
        for göreli, tamam, beklenen, çıkan in havuz.map(örnek, kaynaklar):
            if not tamam:
                başarısız += 1
                print(f"BAŞARISIZ windows örneği: {göreli}")
                print("  beklenen:", repr(beklenen)[:300])
                print("  çıkan:   ", repr(çıkan)[:300])

    # Kendi kendini derleme: nehir.py -> derle1.exe -> derle2.exe -> sabit nokta
    çz = os.path.join(KÖK, "calisma_zamani.s")
    s1, s2, s3 = (os.path.join(dizin, f"derle{i}.s") for i in (1, 2, 3))
    subprocess.run([sys.executable, "nehir.py", "kendi/derle.nehir", "--hedef", "windows", "--asm", "-o", s1],
                   cwd=KÖK, capture_output=True, check=True)
    for kaynak_s, ikili, hedef_s in ((s1, "derle1.exe", s2), (s2, "derle2.exe", s3)):
        ikili = os.path.join(dizin, ikili)
        subprocess.run([gcc, "-nostdlib", "-o", ikili, kaynak_s, "-lkernel32", "-lshell32",
                        "-Wl,-e,_start", "-Wl,--subsystem,console", "-Wl,--stack,67108864"], check=True)
        n = subprocess.run([wine, ikili, "kendi/derle.nehir", hedef_s, çz], cwd=KÖK, capture_output=True, env=ortam)
        if n.returncode != 0:
            print(f"BAŞARISIZ windows kendini derleme: {os.path.basename(ikili)}:", n.stderr[:300])
            return başarısız + 1
    with open(s1, "rb") as a, open(s2, "rb") as b, open(s3, "rb") as c:
        b1, b2, b3 = a.read(), b.read(), c.read()
    if b2 != b1 or b3 != b2:
        başarısız += 1
        print("BAŞARISIZ windows kendini derleme: çıktı nehir.py'ninkinden farklı ya da sabit nokta yok")
    if not başarısız:
        print(f"geçti     windows ({len(kaynaklar)} örnek Wine'da Linux'takiyle aynı çıktıyı veriyor; "
              f"derleyici Windows'ta kendini derleyip sabit noktaya ulaşıyor)")
    return başarısız


def uçbirimde_çalıştır(komut, ortam):
    """Komutu, standart hatası bir sözde uçbirime (pty) bağlı olarak çalıştırır; o uçbirime
    yazılanları bayt bayt verir."""
    import pty
    ana_uç, yan_uç = pty.openpty()
    süreç = subprocess.Popen(komut, cwd=KÖK, stdout=subprocess.DEVNULL, stderr=yan_uç, env=ortam)
    os.close(yan_uç)
    çıktı = b""
    while True:
        try:
            parça = os.read(ana_uç, 65536)
        except OSError:         # yazan taraf kapandı
            break
        if not parça:
            break
        çıktı += parça
    süreç.wait()
    os.close(ana_uç)
    return süreç.returncode, çıktı


def renkleri_sına(geçici):
    """Standart hata bir uçbirimse iki derleyici de hata ve uyarıları aynı renklerle yazmalı;
    NO_COLOR tanımlıysa renksiz yazmalı."""
    ikili = os.path.join(geçici, "derle")       # kendi_kod_üreticiyi_sına'nın derlediği
    dosyalar = ["ornekler/hatalar/tanimsiz_degisken.nehir", "ornekler/hatalar/tanimsiz_islev.nehir",
                "ornekler/hatalar/modul_ad_cakismasi.nehir", "ornekler/hatalar/kapanmamis_metin.nehir",
                "kendi/sinamalar/tani_uyarilar.nehir", "kendi/sinamalar/tani_sekme.nehir",
                "kendi/sinamalar/olmayan.nehir"]
    başarısız = 0
    for ortam_adı, ortam in (("renkli", {k: v for k, v in os.environ.items() if k != "NO_COLOR"}),
                             ("NO_COLOR", dict(os.environ, NO_COLOR=""))):
        for dosya in dosyalar:
            beklenen = uçbirimde_çalıştır([sys.executable, "nehir.py", dosya, "--asm", "-o",
                                           os.path.join(geçici, "r1.s")], ortam)
            çıkan = uçbirimde_çalıştır([ikili, dosya, os.path.join(geçici, "r2.s")], ortam)
            renk_var = b"\x1b[" in beklenen[1]
            if çıkan != beklenen or renk_var != (ortam_adı == "renkli"):
                başarısız += 1
                print(f"BAŞARISIZ renkler ({ortam_adı}): {dosya}")
                print("  beklenen:", repr(beklenen)[:300])
                print("  çıkan:   ", repr(çıkan)[:300])
    if not başarısız:
        print(f"geçti     renkler ({len(dosyalar)} dosyada uçbirimde renkli, NO_COLOR ile renksiz; "
              f"iki derleyici bayt bayt aynı)")
    return başarısız


def tuşları_sına(geçici):
    """tuş_kipi ve tuş() gerçek bir uçbirimde: tuşlar Enter beklemeden ve yankısız gelir,
    kip kapanınca satır okuma ve yankı geri döner; Ctrl+C programı 130 ile bitirir ve
    uçbirimin ayarlarını geri yükler."""
    import pty, select, termios
    ikili = os.path.join(geçici, "tus_kipi")
    subprocess.run([sys.executable, "nehir.py", "kendi/sinamalar/tus_kipi.nehir", "-o", ikili],
                   cwd=KÖK, check=True)
    bırakmalı = os.path.join(geçici, "tus_birakma")
    subprocess.run([sys.executable, "nehir.py", "kendi/sinamalar/tus_birakma.nehir", "-o", bırakmalı],
                   cwd=KÖK, check=True)

    def çalıştır(adımlar, program=ikili):
        ana_uç, yan_uç = pty.openpty()
        önce = termios.tcgetattr(yan_uç)
        süreç = subprocess.Popen([program], stdin=yan_uç, stdout=yan_uç, stderr=yan_uç)
        çıktı = b""

        def bekle(aranan, süre=5):
            nonlocal çıktı
            son = time.time() + süre
            while aranan not in çıktı and time.time() < son:
                if select.select([ana_uç], [], [], 0.05)[0]:
                    try:
                        çıktı += os.read(ana_uç, 4096)
                    except OSError:
                        return
        for aranan, gönderilen in adımlar:
            bekle(aranan)
            os.write(ana_uç, gönderilen)
        try:
            süreç.wait(timeout=5)
        except subprocess.TimeoutExpired:
            süreç.kill()
            süreç.wait()
        bekle(b"\0", 0.2)
        sonra = termios.tcgetattr(yan_uç)
        os.close(yan_uç)
        os.close(ana_uç)
        return süreç.returncode, çıktı.replace(b"\r\n", b"\n"), önce == sonra

    sonuçlar = [
        ("tuşlar ve satır", çalıştır([(b"1\r\n", b"a\x1b[A"), (b"<yukar\xc4\xb1>", b"q"),
                                     (b"0\r\n", b"merhaba\n")]),
         (0, "1\n<a>\n<yukarı>\n0\nmerhaba\nsatır: merhaba\n".encode(), True)),
        ("Ctrl+C", çalıştır([(b"1\r\n", b"x"), (b"<x>", b"\x03")]),
         (130, b"1\n<x>\n\x1b[0m\x1b[?25h\n", True)),
        # kitty klavye protokolü: basma, bırakma ("-a"), Shift'li tuş, tekrar; değiştirici tuş yok sayılır
        ("kitty bırakmaları", çalıştır([(b"1\r\n", b"\x1b[?15u\x1b[97u\x1b[97;1:3u\x1b[1;1:3A\x1b[97:65;2u"
                                                   b"\x1b[57441;2u\x1b[1;1:2A"),
                                        (b"<yukar\xc4\xb1>", b"\x1b[113u")], bırakmalı),
         (0, "\x1b[>15u\x1b[?u1\n<a>\n<-a>\n<-yukarı>\n<A>\n<yukarı>\n1\n\x1b[<u0\n".encode(), True)),
        ("kitty Ctrl+C", çalıştır([(b"1\r\n", b"\x1b[?15u\x1b[98u"), (b"<b>", b"\x1b[99;5u")], bırakmalı),
         (130, b"\x1b[>15u\x1b[?u1\n<b>\n\x1b[0m\x1b[?25h\n\x1b[<u", True)),
    ]
    başarısız = 0
    for ad, çıkan, beklenen in sonuçlar:
        if çıkan != beklenen:
            başarısız += 1
            print(f"BAŞARISIZ tuşlar ({ad})")
            print("  beklenen:", repr(beklenen))
            print("  çıkan:   ", repr(çıkan))
    if not başarısız:
        print("geçti     tuşlar (uçbirimde ham kip: tuşlar beklemeden ve yankısız; kip kapanınca "
              "ve Ctrl+C'de uçbirim eski hâline dönüyor; kitty protokolüyle tuş bırakmaları)")
    return başarısız


def kendini_derlemeyi_sına(geçici):
    """Nehir ile yazılmış derleyici kendini derleyebilmelidir:
      1. nehir.py, kendi/derle.nehir'i (ve kullandığı modülleri) derler      -> derle1
      2. derle1 aynı kaynağı derler; çıktı nehir.py'ninkiyle aynı olmalı     -> derle2
      3. derle2 aynı kaynağı yeniden derler; çıktı değişmemeli (sabit nokta)"""
    kaynak = "kendi/derle.nehir"
    çz = os.path.join(KÖK, "calisma_zamani.s")

    def çevir(s_dosyası, ikili):
        subprocess.run(["as", "-o", ikili + ".o", s_dosyası], check=True)
        subprocess.run(["ld", "-o", ikili, ikili + ".o"], check=True)

    def oku(dosya):
        with open(dosya, "rb") as f:
            return f.read()

    s1, s2, s3 = (os.path.join(geçici, f"derle{i}.s") for i in (1, 2, 3))
    p = subprocess.run([sys.executable, "nehir.py", kaynak, "--asm", "-o", s1], cwd=KÖK,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("BAŞARISIZ kendini derleme: nehir.py derleyicinin kaynağını derleyemedi:", p.stderr.split("\n")[0])
        return 1
    for kaynak_s, ikili, hedef_s in ((s1, "derle1", s2), (s2, "derle2", s3)):
        ikili = os.path.join(geçici, ikili)
        çevir(kaynak_s, ikili)
        n = subprocess.run([ikili, kaynak, hedef_s, çz], cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        if n.returncode != 0:
            print(f"BAŞARISIZ kendini derleme: {os.path.basename(ikili)} kendi kaynağını derleyemedi:",
                  n.stderr.split("\n")[0])
            return 1
    if oku(s2) != oku(s1):
        print("BAŞARISIZ kendini derleme: kendi derlediği derleyici nehir.py'ninkinden farklı")
        return 1
    if oku(s3) != oku(s2):
        print("BAŞARISIZ kendini derleme: sabit noktaya ulaşılmadı (2. ve 3. aşama farklı)")
        return 1
    print(f"geçti     kendini derleme (derleyici kendi kaynağını {oku(s2).count(b'\n')} satır assembly'ye "
          f"nehir.py ile bayt bayt aynı derliyor; sabit noktaya ulaşıldı)")
    return 0


def kendi_kod_üreticiyi_sına(geçici, kaynaklar):
    """Nehir ile yazılmış derleyici (kendi/derle.nehir), Python'daki derleyiciyle bayt bayt
    aynı assembly'yi, aynı hata mesajlarını ve uyarıları, aynı çıkış kodunu vermelidir. Henüz taşınmamış yapıları içeren dosyalarda 3 koduyla çıkar; bunlar sayılır."""
    başarısız = 0
    with open(os.path.join(KÖK, "kendi", "kod_uretici.nehir"), encoding="utf-8") as f:
        kod_üretici = f.read()
    sys.path.insert(0, KÖK)
    import nehir
    eksik = [ad for ad, asıl in nehir.YERLEŞİKLER.items() if f'"{ad}": "{asıl}"' not in kod_üretici]
    if eksik:
        başarısız += 1
        print("BAŞARISIZ kendi/kod_uretici.nehir şu yerleşik adları bilmiyor:", ", ".join(eksik))
    eksik = [satır for satır in nehir.RİSKLİ if f'"{satır}": 1' not in kod_üretici]
    if eksik:
        başarısız += 1
        print("BAŞARISIZ kendi/kod_uretici.nehir'deki RİSKLİ tablosunda eksikler:", ", ".join(eksik))
    with open(os.path.join(KÖK, "kendi", "sozcukleyici.nehir"), encoding="utf-8") as f:
        sözcükleyici = f.read()
    if subprocess.run([sys.executable, os.path.join(KÖK, "kendi", "veri_uret.py"), "--denetle"]).returncode:
        başarısız += 1
        print("BAŞARISIZ kendi/veri.nehir güncel değil: python3 kendi/veri_uret.py ile yeniden üretin")
    eksik = [ad for ad, asıl in nehir.ANAHTARLAR.items() if f'"{ad}": "{asıl}"' not in sözcükleyici]
    if eksik:
        başarısız += 1
        print("BAŞARISIZ kendi/sozcukleyici.nehir şu anahtar kelimeleri bilmiyor:", ", ".join(eksik))
    if f'"{nehir.YIĞIN_BOYUTU}" -> YIĞIN_BOYUTU' not in kod_üretici:
        başarısız += 1
        print("BAŞARISIZ kendi/kod_uretici.nehir'deki YIĞIN_BOYUTU nehir.py'dekiyle aynı değil")

    ikili = os.path.join(geçici, "derle")
    s = subprocess.run([sys.executable, "nehir.py", "kendi/derle.nehir", "-o", ikili],
                       cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
    if s.returncode != 0:
        print("BAŞARISIZ kendi/derle.nehir derlenemedi:", s.stderr.split("\n")[0])
        return başarısız + 1

    aynı = desteklenmeyen = derlenen = 0
    for kaynak in kaynaklar:
        göreli = os.path.relpath(kaynak, KÖK).replace(os.sep, "/")
        py_s, nh_s = os.path.join(geçici, "py.s"), os.path.join(geçici, "nh.s")
        for yol in (py_s, nh_s):
            if os.path.exists(yol):
                os.remove(yol)
        p = subprocess.run([sys.executable, "nehir.py", göreli, "--asm", "-o", py_s],
                           cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        n = subprocess.run([ikili, göreli, nh_s], cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        if n.returncode == 3:
            desteklenmeyen += 1
            continue
        # Hata mesajları (kaynak satırı, ipucu ve notlarıyla) ve uyarılar da aynı olmalı.
        beklenen = (p.returncode, p.stderr)
        çıkan = (n.returncode, n.stderr)
        if beklenen == çıkan and p.returncode == 0:
            with open(py_s, "rb") as a, open(nh_s, "rb") as b:
                if a.read() != b.read():
                    çıkan = (n.returncode, "(assembly farklı)")
        if beklenen != çıkan:
            başarısız += 1
            print(f"BAŞARISIZ kendi kod üretici: {göreli}")
            print("  beklenen:", repr(beklenen)[:300])
            print("  çıkan:   ", repr(çıkan)[:300])
            continue
        aynı += 1
        derlenen += p.returncode == 0
    if not başarısız:
        print(f"geçti     kendi kod üretici ({aynı} dosyada Python ile aynı sonuç, {derlenen} tanesi "
              f"bayt bayt aynı assembly; {desteklenmeyen} dosya henüz taşınmamış yapılar içeriyor)")
    return başarısız


if __name__ == "__main__":
    sys.exit(ana())
