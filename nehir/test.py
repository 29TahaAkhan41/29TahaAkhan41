#!/usr/bin/env python3
"""ornekler/ altındaki her .nehir dosyasını derler, çalıştırır ve çıktısını
yanındaki .beklenen dosyasıyla karşılaştırır.

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
        for kaynak in sorted(glob.glob(os.path.join(KÖK, "ornekler", "*.nehir"))):
            ad = os.path.splitext(os.path.basename(kaynak))[0]
            beklenen_yolu = os.path.splitext(kaynak)[0] + ".beklenen"
            sonuç = subprocess.run(
                [sys.executable, os.path.join(KÖK, "nehir.py"), kaynak,
                 "-o", os.path.join(geçici, ad), "--run"],
                capture_output=True, text=True)
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
    return 1 if başarısız else 0


if __name__ == "__main__":
    sys.exit(ana())
