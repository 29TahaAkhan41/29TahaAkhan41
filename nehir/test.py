#!/usr/bin/env python3
"""ornekler/ ve ornekler/hatalar/ altındaki her .nehir dosyasını derler, çalıştırır
ve çıktısını (hata mesajları dahil) yanındaki .beklenen dosyasıyla karşılaştırır. Aynı adlı bir .girdi dosyası varsa
programa standart girdi olarak verilir.

Ardından Nehir ile yazılmış sözcükleyiciyi (kendi/sozcukleyici.nehir) derler ve
bütün .nehir dosyalarında Python'daki sözcükleyiciyle aynı çıktıyı verdiğini sınar.

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
            başarısız += kendi_sözcükleyiciyi_sına(geçici, kaynaklar)
    return 1 if başarısız else 0


def kendi_sözcükleyiciyi_sına(geçici, kaynaklar):
    """Nehir ile yazılmış sözcükleyici, her dosyada Python'dakiyle aynı sözcükleri
    (hatalı dosyalarda aynı ilk hata satırını ve çıkış kodunu) vermelidir."""
    def çalıştır(komut):
        s = subprocess.run(komut, cwd=KÖK, capture_output=True, text=True, encoding="utf-8")
        ilk_hata = s.stderr.split("\n")[0]
        return s.returncode, s.stdout, ilk_hata

    ikili = os.path.join(geçici, "sozcukleyici")
    kod, _, hata = çalıştır([sys.executable, "nehir.py", "kendi/sozcukleyici.nehir", "-o", ikili])
    if kod != 0:
        print("BAŞARISIZ kendi/sozcukleyici derlenemedi:", hata)
        return 1
    başarısız = 0
    kaynaklar = kaynaklar + sorted(glob.glob(os.path.join(KÖK, "kendi", "*.nehir"))) + \
        sorted(glob.glob(os.path.join(KÖK, "kendi", "sinamalar", "*.nehir")))
    for kaynak in kaynaklar:
        göreli = os.path.relpath(kaynak, KÖK).replace(os.sep, "/")
        beklenen = çalıştır([sys.executable, "nehir.py", göreli, "--sözcükler"])
        çıkan = çalıştır([ikili, göreli])
        if çıkan != beklenen:
            başarısız += 1
            print(f"BAŞARISIZ kendi sözcükleyici: {göreli}")
            for b, ç in zip(beklenen, çıkan):
                if b != ç:
                    print("  beklenen:", repr(b)[:300])
                    print("  çıkan:   ", repr(ç)[:300])
                    break
    if not başarısız:
        print(f"geçti     kendi sözcükleyici ({len(kaynaklar)} dosyada Python ile aynı çıktı)")
    return başarısız


if __name__ == "__main__":
    sys.exit(ana())
