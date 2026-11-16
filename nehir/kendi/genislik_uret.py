#!/usr/bin/env python3
"""calisma_zamani.s'deki uçbirim genişliği tablolarını (ekran tamponu için) üretir:
Doğu Asya geniş/tam genişlikli karakterler (2 sütun) ve birleşen işaretler ile biçim
karakterleri (0 sütun). Tablolar yorum işaretleri arasına yazılır.

  python3 kendi/genislik_uret.py
"""
import os
import unicodedata

YOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calisma_zamani.s")
BAŞ, SON = "# >>> genişlik tabloları", "# <<< genişlik tabloları"


def aralıklar(koşul):
    sonuç, baş = [], None
    for kod in range(0x110000):
        if koşul(kod):
            if baş is None:
                baş = kod
        elif baş is not None:
            sonuç.append((baş, kod - 1))
            baş = None
    if baş is not None:
        sonuç.append((baş, 0x10FFFF))
    return sonuç


def tablo(ad, aralıklar_):
    satırlar = ["    .balign 8", f"{ad}_sayi: .quad {len(aralıklar_)}", f"{ad}:"]
    for i in range(0, len(aralıklar_), 6):
        satırlar.append("    .long " + ", ".join(f"0x{a:X}, 0x{b:X}" for a, b in aralıklar_[i:i + 6]))
    return satırlar


def üret():
    iki = aralıklar(lambda k: unicodedata.east_asian_width(chr(k)) in "WF")
    sıfır = aralıklar(lambda k: k >= 0x300 and unicodedata.category(chr(k)) in ("Mn", "Me", "Cf"))
    return [BAŞ, f"# Unicode {unicodedata.unidata_version}; kendi/genislik_uret.py ile üretildi"] \
        + tablo("__gen_iki", iki) + tablo("__gen_sifir", sıfır) + [SON]


if __name__ == "__main__":
    with open(YOL, encoding="utf-8") as f:
        metin = f.read()
    yeni = "\n".join(üret())
    if BAŞ in metin:
        i, j = metin.index(BAŞ), metin.index(SON) + len(SON)
        metin = metin[:i] + yeni + metin[j:]
    else:
        metin = metin.rstrip("\n") + "\n\n    .section .rodata\n" + yeni + "\n"
    with open(YOL, "w", encoding="utf-8") as f:
        f.write(metin)
