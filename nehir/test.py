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
    return başarısız + kendi_kod_üreticiyi_sına(geçici, kaynaklar) + kendini_derlemeyi_sına(geçici)


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
