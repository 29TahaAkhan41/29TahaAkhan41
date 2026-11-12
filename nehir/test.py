#!/usr/bin/env python3
"""ornekler/ ve ornekler/hatalar/ altındaki her .nehir dosyasını derler, çalıştırır
ve çıktısını (hata mesajları dahil) yanındaki .beklenen dosyasıyla karşılaştırır. Aynı adlı bir .girdi dosyası varsa
programa standart girdi olarak verilir.

Ardından Nehir ile yazılmış derleyici aşamalarını (kendi/ altındaki sözcükleyici ve
ayrıştırıcı) derler ve bütün .nehir dosyalarında Python'daki karşılıklarıyla aynı
çıktıyı verdiklerini sınar.

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
    """Nehir ile yazılmış aşamalar, her dosyada Python'daki karşılıklarıyla aynı çıktıyı
    (hatalı dosyalarda aynı ilk hata satırını ve çıkış kodunu) vermelidir."""
    def çalıştır(komut):
        s = subprocess.run(komut, cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        ilk_hata = s.stderr.split("\n")[0]
        return s.returncode, s.stdout, ilk_hata

    kaynaklar = list(kaynaklar)
    for kalıp in ("ornekler/moduller/*.nehir", "ornekler/hatalar/moduller/*.nehir",
                  "kendi/*.nehir", "kendi/sinamalar/*.nehir"):
        kaynaklar += sorted(glob.glob(os.path.join(KÖK, *kalıp.split("/"))))

    başarısız = 0
    # Ayrıştırıcının bildiği yerleşik ad listesi derleyicininkiyle aynı kalmalı.
    sys.path.insert(0, KÖK)
    import nehir
    with open(os.path.join(KÖK, "kendi", "ayristirici.nehir"), encoding="utf-8") as f:
        ayrıştırıcı_kaynağı = f.read()
    eksik = [ad for ad in nehir.YERLEŞİKLER if f'"{ad}": 1' not in ayrıştırıcı_kaynağı]
    if eksik:
        başarısız += 1
        print("BAŞARISIZ kendi/ayristirici.nehir şu yerleşik adları bilmiyor:", ", ".join(eksik))

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
    return başarısız


if __name__ == "__main__":
    sys.exit(ana())
