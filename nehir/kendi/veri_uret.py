#!/usr/bin/env python3
"""kendi/veri.nehir dosyasını üretir: Nehir ile yazılmış derleyicinin, nehir.py ile aynı
davranabilmesi için Python'dan aldığı veriler.

  - Unicode karakter sınıfları (str.isalpha, isalnum, isspace, isprintable) aralıklar olarak
  - işletim sistemi hata metinleri (os.strerror)

Bu veriler çalışan Python'un sürümüne bağlıdır; test.py, dosyanın güncel olduğunu denetler.

  python3 kendi/veri_uret.py           dosyayı yeniden yaz
  python3 kendi/veri_uret.py --denetle  dosya güncel değilse 1 ile çık
"""
import os
import sys
import unicodedata

YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri.nehir")


def aralıklar(koşul):
    """Koşulu sağlayan kod noktalarının aralıkları: "a-b,c-d,...". ASCII de dahildir."""
    sonuç, baş = [], None
    for kod in range(sys.maxunicode + 1):
        if koşul(chr(kod)):
            if baş is None:
                baş = kod
        elif baş is not None:
            sonuç.append(f"{baş}-{kod - 1}")
            baş = None
    if baş is not None:
        sonuç.append(f"{baş}-{sys.maxunicode}")
    return ",".join(sonuç)


def metin(m):
    return '"' + m.replace("\\", "\\\\").replace('"', '\\"') + '"'


def üret():
    satırlar = [
        "# Bu dosya kendi/veri_uret.py ile üretilir; elle değiştirmeyin.",
        f"# Unicode {unicodedata.unidata_version} (Python {sys.version.split()[0]})",
        "",
        "# Unicode karakter sınıfları, \"baş-son\" kod noktası aralıkları olarak (onluk).",
        f"{metin(aralıklar(str.isalpha))} -> U_HARF            # str.isalpha",
        f"{metin(aralıklar(str.isalnum))} -> U_HARF_RAKAM      # str.isalnum",
        f"{metin(aralıklar(str.isspace))} -> U_BOŞLUK          # str.isspace",
        f"{metin(aralıklar(lambda c: not c.isprintable()))} -> U_YAZDIRILAMAZ    # değil str.isprintable",
        "",
        "# İşletim sistemi hata metinleri (os.strerror)",
        "{",
    ]
    hatalar = [f"    {n}: {metin(os.strerror(n))}" for n in range(1, 134)]
    satırlar.append(",\n".join(hatalar))
    satırlar.append("} -> SİSTEM_HATALARI")
    return "\n".join(satırlar) + "\n"


if __name__ == "__main__":
    yeni = üret()
    if "--denetle" in sys.argv:
        with open(YOL, encoding="utf-8") as f:
            sys.exit(0 if f.read() == yeni else 1)
    with open(YOL, "w", encoding="utf-8") as f:
        f.write(yeni)
