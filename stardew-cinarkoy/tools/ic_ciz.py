#!/usr/bin/env python3
"""Çınarköy ev içlerinin karolarını sıfırdan çizer: zemin, duvar, mobilya.

Oyunun görsellerinden hiçbir piksel kullanmaz.
Çıktı: [CP] Cinarkoy/assets/cinarkoy_ic.png

    python3 tools/ic_ciz.py

ic_uret.py bu dosyayı içe aktarır; sayfa() her parçanın karo setindeki yerini verir.
"""
from PIL import Image, ImageDraw

from ev_ciz import (AHIR, AHSAP, ASSETS, BAL, BEYAZ, C_GRI, C_KIRMIZI, CAM, KENAR, SIVA, TAS, TUGLA,
                    Tuval, zar)

BOSLUK = (22, 14, 26)                                   # oda dışındaki karanlık
DOSEME = [(96, 56, 30), (150, 96, 52), (186, 128, 72), (212, 158, 96), (236, 190, 128)]
SAMAN = [(150, 110, 40), (206, 162, 66), (236, 200, 96), (250, 226, 140), (255, 244, 190)]
DUVAR_KREM = [(170, 150, 120), (222, 206, 172), (240, 228, 198), (250, 242, 220), (255, 252, 240)]
DUVAR_MAVI = [(84, 110, 140), (140, 170, 196), (176, 204, 224), (206, 226, 240), (232, 244, 252)]
DUVAR_YESIL = [(84, 122, 92), (140, 178, 140), (178, 208, 172), (208, 230, 200), (232, 246, 226)]
DUVAR_PEMBE = [(150, 100, 110), (206, 160, 164), (232, 196, 196), (246, 222, 220), (255, 242, 240)]
YORGAN_MAVI = [(34, 60, 110), (64, 106, 170), (118, 160, 216)]
YORGAN_KIRMIZI = [(110, 24, 30), (190, 54, 52), (236, 110, 96)]
YORGAN_YESIL = [(28, 80, 50), (56, 136, 78), (110, 188, 110)]
YORGAN_SARI = [(170, 110, 30), (242, 196, 70), (255, 236, 150)]
YORGAN_MOR = [(64, 30, 70), (118, 62, 124), (170, 112, 176)]


def yeni(gk, yk):
    return Tuval(gk, yk)


# ------------------------------------------------------------------ zemin ---
def zemin_tahta():
    """4x2 karoluk, kendini tekrarlayan döşeme tahtası."""
    t = yeni(4, 2)
    for y in range(32):
        s, iy = y // 8, y % 8
        for x in range(64):
            ek = (x + (16 if s % 2 else 0)) % 32
            tahta = ((x + (16 if s % 2 else 0)) // 32) % 2 + s * 2
            ton = 2 + (zar(tahta, 31) > 0.6)
            if iy == 7 or ek == 31:
                c = DOSEME[0]
            elif iy == 0:
                c = DOSEME[ton + 1]
            elif zar(x // 3, y, 33) > 0.94:
                c = DOSEME[ton - 1]
            else:
                c = DOSEME[ton]
            t.nokta(x, y, c)
    return t.im


def zemin_tas():
    t = yeni(4, 2)
    for y in range(32):
        s, iy = y // 8, y % 8
        for x in range(64):
            xx = (x + (8 if s % 2 else 0)) % 64
            ix, tas = xx % 16, xx // 16 + s * 4
            ton = 2 + (zar(tas, 41) > 0.65) - (zar(tas, 42) > 0.8)
            if iy == 7 or ix == 15:
                c = TAS[0]
            elif iy == 0 or ix == 0:
                c = TAS[ton + 1]
            elif zar(x, y, 43) > 0.96:
                c = TAS[ton - 1]
            else:
                c = TAS[ton]
            t.nokta(x, y, c)
    return t.im


def zemin_saman():
    t = yeni(4, 2)
    t.r(0, 0, 63, 31, SAMAN[1])
    for i in range(150):
        x, y = int(zar(i, 51) * 64), int(zar(i, 52) * 32)
        uz = 2 + int(zar(i, 53) * 4)
        c = SAMAN[(0, 2, 3, 2)[i % 4]]
        for k in range(uz):
            t.nokta((x + k) % 64, (y + (k // 2 if i % 3 else -k // 2)) % 32, c)
    return t.im


# ------------------------------------------------------------------ duvar ---
def duvar(P, stil="duz"):
    """1x3 karoluk arka duvar dilimi: tavan pervazı, duvar, süpürgelik."""
    t = yeni(1, 3)
    t.r(0, 0, 15, 47, P[2])
    for y in range(4, 40):
        for x in range(16):
            if stil == "cizgili":
                c = P[3] if (x // 4) % 2 else P[2]
                if x % 4 == 0:
                    c = P[1]
            elif stil == "tahta":
                i = x % 8
                c = P[3] if i == 0 else P[0] if i == 7 else P[1] if zar(x, y // 3, 61) > 0.93 else P[2]
            else:
                z = zar(x, y, 62)
                c = P[1] if z > 0.97 else P[3] if z < 0.03 else P[2]
            t.nokta(x, y, c)
    for y in range(4, 9):                               # tavandan düşen gölge
        for x in range(16):
            t.karart(x, y, 0.80 if y < 7 else 0.90)
    t.r(0, 0, 15, 3, AHSAP[1])
    t.cizgi(0, 0, 15, 0, AHSAP[0])
    t.cizgi(0, 1, 15, 1, AHSAP[3])
    t.cizgi(0, 3, 15, 3, AHSAP[0])
    t.r(0, 40, 15, 47, AHSAP[2])
    t.cizgi(0, 40, 15, 40, AHSAP[0])
    t.cizgi(0, 41, 15, 41, AHSAP[4])
    t.cizgi(0, 46, 15, 46, AHSAP[1])
    t.cizgi(0, 47, 15, 47, AHSAP[0])
    return t.im


def kenar(tur):
    """Odayı çevreleyen karanlık kenar karoları."""
    t = yeni(1, 1)
    t.r(0, 0, 15, 15, BOSLUK)

    def pervaz(yatay, bas):
        for k, c in enumerate((AHSAP[0], AHSAP[2], AHSAP[1], AHSAP[0])):
            if yatay:
                t.cizgi(0, bas + k, 15, bas + k, c)
            else:
                t.cizgi(bas + k, 0, bas + k, 15, c)
    if tur in ("sol", "alt_sol"):
        pervaz(False, 12)
    if tur in ("sag", "alt_sag"):
        pervaz(False, 0)
    if tur in ("alt", "alt_sol", "alt_sag"):
        if tur == "alt":
            pervaz(True, 0)
        elif tur == "alt_sol":
            for k, c in enumerate((AHSAP[0], AHSAP[2], AHSAP[1], AHSAP[0])):
                t.cizgi(12, k, 15, k, c)
        else:
            for k, c in enumerate((AHSAP[0], AHSAP[2], AHSAP[1], AHSAP[0])):
                t.cizgi(0, k, 3, k, c)
    return t.im


# ---------------------------------------------------------------- mobilya ---
def yatak(Y):
    t = yeni(2, 3)
    t.cerceve(3, 2, 28, 12, AHSAP)                       # başlık
    t.cizgi(6, 5, 25, 5, AHSAP[4])
    t.r(3, 13, 28, 43, BEYAZ[3])                         # çarşaf
    t.d.rectangle([2, 12, 29, 44], outline=AHSAP[0] + (255,))
    t.r(7, 14, 24, 21, BEYAZ[4])                         # yastık
    t.d.rectangle([7, 14, 24, 21], outline=BEYAZ[1] + (255,))
    t.cizgi(9, 20, 22, 20, BEYAZ[2])
    t.r(3, 23, 28, 43, Y[1])                             # yorgan
    t.r(3, 23, 28, 25, Y[2])
    t.cizgi(3, 26, 28, 26, Y[0])
    for x in range(7, 28, 7):
        t.cizgi(x, 28, x, 42, Y[0])
    for y in range(31, 42, 6):
        t.cizgi(4, y, 27, y, Y[2])
    t.r(24, 23, 28, 43, tuple(int(v * 0.85) for v in Y[1]))
    t.cerceve(3, 43, 28, 46, AHSAP)                      # ayak ucu
    return t.bitir()


def masa(ortu=None):
    t = yeni(2, 2)
    t.r(5, 22, 7, 30, AHSAP[1])                          # bacaklar
    t.r(24, 22, 26, 30, AHSAP[1])
    t.r(2, 6, 29, 19, BAL[3])                            # tabla
    t.cizgi(2, 6, 29, 6, BAL[4])
    for y in (10, 14):
        t.cizgi(3, y, 28, y, BAL[2])
    t.r(2, 20, 29, 23, BAL[1])
    t.cizgi(2, 20, 29, 20, BAL[0])
    t.d.rectangle([1, 5, 30, 24], outline=AHSAP[0] + (255,))
    if ortu:
        t.r(8, 7, 23, 18, ortu[2])
        t.d.rectangle([8, 7, 23, 18], outline=ortu[1] + (255,))
        for x in range(10, 23, 4):
            t.cizgi(x, 8, x, 17, ortu[1])
    t.d.ellipse([12, 9, 19, 15], fill=BEYAZ[3] + (255,), outline=BEYAZ[1] + (255,))   # tabak
    t.r(14, 11, 17, 13, (214, 120, 60))
    return t.bitir()


def tabure():
    t = yeni(1, 1)
    t.r(3, 9, 4, 14, AHSAP[1])
    t.r(11, 9, 12, 14, AHSAP[1])
    t.d.ellipse([2, 3, 13, 10], fill=BAL[3] + (255,), outline=AHSAP[0] + (255,))
    t.cizgi(5, 5, 10, 5, BAL[4])
    return t.bitir()


def somine(P=TAS):
    t = yeni(2, 3)
    dok = __import__("ev_ciz").dok_tas(32, 48, P, 6, sy=6) if P is TAS else __import__("ev_ciz").dok_tugla(32, 48, P, 6)
    t.doku(dok, [(2, 4), (29, 4), (29, 47), (2, 47)])
    t.r(0, 16, 31, 20, AHSAP[2])                         # raf
    t.cizgi(0, 16, 31, 16, AHSAP[4])
    t.cizgi(0, 20, 31, 20, AHSAP[0])
    t.r(7, 26, 24, 47, (30, 20, 26))                     # ocak ağzı
    t.d.rectangle([6, 25, 25, 47], outline=P[0] + (255,))
    for x0, h, c in ((10, 12, (230, 90, 40)), (15, 16, (250, 150, 50)), (19, 10, (230, 90, 40)), (13, 8, (255, 220, 110)), (17, 9, (255, 230, 130))):
        t.d.polygon([(x0 - 3, 46), (x0, 46 - h), (x0 + 3, 46)], fill=c + (255,))
    t.r(8, 44, 23, 46, (90, 50, 30))                     # odun
    t.cizgi(8, 44, 23, 44, (140, 84, 44))
    t.r(11, 10, 14, 15, (60, 130, 90))                   # raftaki süsler
    t.r(19, 12, 22, 15, (214, 170, 80))
    return t.bitir()


def kitaplik():
    t = yeni(2, 3)
    t.cerceve(2, 4, 29, 46, AHSAP)
    renkler = [(190, 54, 52), (64, 106, 170), (56, 136, 78), (242, 196, 70), (118, 62, 124), (214, 120, 60)]
    for s, y0 in enumerate((7, 20, 33)):
        t.r(4, y0, 27, y0 + 10, (48, 26, 26))
        x = 5
        i = s * 3
        while x < 26:
            g = 2 + int(zar(x, s, 71) * 2)
            h = 7 + int(zar(x, s, 72) * 3)
            c = renkler[i % len(renkler)]
            t.r(x, y0 + 10 - h, min(x + g, 26), y0 + 10, c)
            t.cizgi(x, y0 + 10 - h, x, y0 + 10, tuple(min(255, v + 40) for v in c))
            x += g + 1
            i += 1
        t.cizgi(3, y0 + 11, 28, y0 + 11, AHSAP[4])
    return t.bitir()


def dolap():
    t = yeni(2, 2)
    t.cerceve(2, 4, 29, 29, AHSAP)
    t.r(1, 3, 30, 6, BAL[3])
    t.cizgi(1, 3, 30, 3, BAL[4])
    t.cizgi(1, 7, 30, 7, AHSAP[0])
    for y0 in (10, 19):
        t.d.rectangle([5, y0, 26, y0 + 7], outline=AHSAP[0] + (255,), fill=AHSAP[3] + (255,))
        t.r(14, y0 + 3, 17, y0 + 4, (255, 214, 92))
    return t.bitir()


def pencere(perde):
    t = yeni(1, 2)
    t.r(1, 5, 14, 26, AHSAP[3])
    t.d.rectangle([1, 5, 14, 26], outline=AHSAP[0] + (255,))
    t.r(3, 7, 12, 24, CAM[1])
    t.r(3, 7, 12, 14, CAM[2])
    t.cizgi(3, 16, 12, 16, AHSAP[3])
    t.r(7, 7, 8, 24, AHSAP[3])
    for i in range(3):
        t.nokta(4 + i, 11 - i, CAM[3])
    for x in (3, 4, 11, 12):                              # perdeler
        t.cizgi(x, 7, x, 22, perde[1] if x in (3, 12) else perde[2])
    t.r(0, 26, 15, 27, AHSAP[4])
    t.cizgi(0, 28, 15, 28, AHSAP[0])
    return t.im


def tablo():
    t = yeni(1, 1)
    t.r(2, 3, 13, 12, (150, 206, 236))
    t.r(2, 9, 13, 12, (86, 160, 80))
    t.d.polygon([(4, 9), (7, 5), (10, 9)], fill=(120, 130, 150, 255))
    t.nokta(11, 5, (255, 236, 150))
    t.d.rectangle([1, 2, 14, 13], outline=BAL[1] + (255,))
    t.d.rectangle([0, 1, 15, 14], outline=AHSAP[0] + (255,))
    return t.im


def saksi():
    t = yeni(1, 2)
    for x0, y0, x1, y1 in ((3, 4, 12, 13), (1, 9, 8, 17), (8, 8, 14, 17), (5, 1, 10, 8)):
        t.d.ellipse([x0, y0, x1, y1], fill=(56, 136, 78, 255), outline=(28, 80, 50, 255))
    for x, y in ((6, 6), (4, 12), (11, 11), (8, 3)):
        t.nokta(x, y, (110, 188, 110))
    t.d.polygon([(3, 18), (12, 18), (10, 30), (5, 30)], fill=(190, 96, 52, 255), outline=AHSAP[0] + (255,))
    t.cizgi(3, 18, 12, 18, (232, 140, 86))
    return t.bitir()


def hali(P):
    t = yeni(3, 2)
    t.r(0, 0, 47, 31, P[1])
    t.d.rectangle([0, 0, 47, 31], outline=P[0] + (255,))
    t.d.rectangle([3, 3, 44, 28], outline=P[2] + (255,))
    t.d.rectangle([6, 6, 41, 25], outline=P[0] + (255,))
    for x in range(10, 40, 8):
        t.d.polygon([(x, 15), (x + 3, 11), (x + 6, 15), (x + 3, 19)], fill=P[2] + (255,))
    for x in range(1, 47, 3):
        t.nokta(x, 0, P[2])
        t.nokta(x, 31, P[2])
    return t.im


def paspas(zemin):
    t = yeni(1, 1)
    t.im.paste(zemin.crop((0, 0, 16, 16)))
    t.r(1, 4, 14, 13, (120, 70, 40))
    t.d.rectangle([1, 4, 14, 13], outline=AHSAP[0] + (255,))
    for x in range(3, 13, 2):
        t.cizgi(x, 6, x, 11, (176, 116, 66))
    return t.im


def tezgah(parca):
    """Dükkân tezgâhı: sol / orta / sağ parçalar, her biri 1x2."""
    t = yeni(1, 2)
    x0 = 2 if parca == "sol" else 0
    x1 = 13 if parca == "sag" else 15
    t.r(x0, 6, x1, 16, BAL[3])
    t.cizgi(x0, 6, x1, 6, BAL[4])
    t.cizgi(x0, 16, x1, 16, AHSAP[0])
    t.r(x0, 17, x1, 30, AHSAP[2])
    for x in range(x0 + 3, x1, 6):
        t.cizgi(x, 18, x, 29, AHSAP[1])
    t.cizgi(x0, 17, x1, 17, AHSAP[3])
    t.cizgi(x0, 30, x1, 30, AHSAP[0])
    t.cizgi(x0, 5, x1, 5, AHSAP[0])
    if parca == "sol":
        t.cizgi(x0 - 1, 5, x0 - 1, 30, AHSAP[0])
    if parca == "sag":
        t.cizgi(x1 + 1, 5, x1 + 1, 30, AHSAP[0])
    if parca == "orta":
        t.r(5, 1, 11, 8, (90, 96, 110))                   # terazi
        t.r(3, 8, 13, 9, (150, 156, 170))
        t.nokta(8, 3, (255, 214, 92))
    return t.im


def mal_rafi(tohum):
    t = yeni(2, 3)
    t.cerceve(2, 4, 29, 46, BAL)
    renkler = [(214, 72, 60), (240, 190, 70), (110, 170, 70), (150, 100, 190), (236, 226, 204), (64, 106, 170)]
    for s, y0 in enumerate((7, 20, 33)):
        t.r(4, y0, 27, y0 + 10, (60, 36, 30))
        for i, x in enumerate(range(5, 25, 6)):
            c = renkler[int(zar(x, s, tohum) * len(renkler))]
            if (i + s + tohum) % 2:
                t.r(x, y0 + 4, x + 4, y0 + 10, c)                         # kutu
                t.cizgi(x, y0 + 4, x + 4, y0 + 4, tuple(min(255, v + 40) for v in c))
            else:
                t.d.ellipse([x, y0 + 3, x + 4, y0 + 10], fill=c + (255,))   # kavanoz
                t.r(x + 1, y0 + 2, x + 3, y0 + 3, (236, 226, 204))
        t.cizgi(3, y0 + 11, 28, y0 + 11, BAL[4])
    return t.bitir()


def fici():
    t = yeni(1, 2)
    t.d.rounded_rectangle([2, 8, 13, 30], radius=3, fill=BAL[2] + (255,), outline=AHSAP[0] + (255,))
    for x in (5, 8, 11):
        t.cizgi(x, 10, x, 29, BAL[1])
    t.cizgi(3, 10, 3, 28, BAL[4])
    for y in (12, 26):
        t.r(2, y, 13, y + 1, C_GRI[2])
        t.cizgi(2, y, 13, y, C_GRI[4])
    t.d.ellipse([3, 6, 12, 11], fill=BAL[3] + (255,), outline=AHSAP[0] + (255,))
    return t.bitir()


def sandik():
    t = yeni(1, 1)
    t.cerceve(2, 3, 13, 14, BAL)
    t.cizgi(3, 4, 12, 13, BAL[1])
    t.cizgi(12, 4, 3, 13, BAL[1])
    t.d.rectangle([4, 5, 11, 12], outline=BAL[1] + (255,))
    return t.bitir()


def cuval():
    t = yeni(1, 1)
    t.d.ellipse([2, 4, 13, 15], fill=(214, 190, 140, 255), outline=(120, 92, 56, 255))
    t.r(6, 1, 9, 4, (214, 190, 140))
    t.cizgi(5, 4, 10, 4, (120, 92, 56))
    t.cizgi(5, 9, 10, 9, (176, 150, 100))
    return t.bitir()


def saman_balyasi():
    t = yeni(2, 2)
    t.r(2, 6, 29, 29, SAMAN[2])
    for i in range(70):
        x, y = 3 + int(zar(i, 81) * 25), 7 + int(zar(i, 82) * 22)
        t.cizgi(x, y, min(x + 3, 28), y, SAMAN[(1, 3, 4)[i % 3]])
    t.r(2, 6, 29, 9, SAMAN[3])
    for x in (10, 21):
        t.r(x, 6, x + 1, 29, AHSAP[2])
    t.d.rectangle([1, 5, 30, 30], outline=SAMAN[0] + (255,))
    return t.bitir()


def yalak():
    t = yeni(2, 1)
    t.cerceve(2, 4, 29, 13, AHSAP)
    t.r(4, 5, 27, 9, (70, 130, 190))
    t.cizgi(6, 6, 14, 6, (160, 216, 234))
    t.d.rectangle([4, 5, 27, 9], outline=AHSAP[0] + (255,))
    return t.bitir()


def bolme():
    """Ahır bölmesi çiti, 1x2; yan yana dizilir."""
    t = yeni(1, 2)
    for y in (10, 18, 26):
        t.r(0, y, 15, y + 2, BAL[2])
        t.cizgi(0, y, 15, y, BAL[4])
        t.cizgi(0, y + 3, 15, y + 3, AHSAP[0])
    t.r(6, 6, 9, 31, BAL[1])
    t.cizgi(6, 6, 6, 31, BAL[3])
    t.d.rectangle([5, 5, 10, 31], outline=AHSAP[0] + (255,))
    return t.im


def marangoz_tezgahi():
    t = yeni(3, 2)
    t.r(4, 20, 7, 30, AHSAP[1])
    t.r(40, 20, 43, 30, AHSAP[1])
    t.r(2, 8, 45, 18, BAL[2])
    t.cizgi(2, 8, 45, 8, BAL[4])
    t.r(2, 19, 45, 22, BAL[1])
    t.d.rectangle([1, 7, 46, 23], outline=AHSAP[0] + (255,))
    t.r(8, 10, 26, 13, BAL[4])                           # rendelenen tahta
    t.d.rectangle([8, 10, 26, 13], outline=BAL[1] + (255,))
    t.r(30, 9, 41, 11, C_GRI[3])                         # testere
    for x in range(30, 42, 2):
        t.nokta(x, 12, C_GRI[1])
    t.r(41, 8, 44, 12, AHSAP[2])
    t.r(12, 15, 15, 17, C_GRI[2])                        # çekiç
    t.cizgi(16, 16, 22, 16, AHSAP[3])
    return t.bitir()


def odun_yigini():
    t = yeni(2, 2)
    for s, (y, x0) in enumerate(((22, 2), (14, 5), (6, 9))):
        for x in range(x0, 30 - x0 + 2, 8):
            t.d.ellipse([x, y, x + 8, y + 8], fill=BAL[3] + (255,), outline=AHSAP[0] + (255,))
            t.d.ellipse([x + 2, y + 2, x + 6, y + 6], outline=BAL[1] + (255,))
            t.nokta(x + 4, y + 4, BAL[1])
    return t.bitir()


PARCALAR = {
    "zemin_tahta": zemin_tahta, "zemin_tas": zemin_tas, "zemin_saman": zemin_saman,
    "duvar_krem": lambda: duvar(DUVAR_KREM), "duvar_mavi": lambda: duvar(DUVAR_MAVI, "cizgili"),
    "duvar_yesil": lambda: duvar(DUVAR_YESIL, "cizgili"), "duvar_pembe": lambda: duvar(DUVAR_PEMBE, "cizgili"),
    "duvar_tahta": lambda: duvar(BAL, "tahta"), "duvar_ahir": lambda: duvar(AHIR, "tahta"),
    "bosluk": lambda: kenar("bos"), "kenar_sol": lambda: kenar("sol"), "kenar_sag": lambda: kenar("sag"),
    "kenar_alt": lambda: kenar("alt"), "kenar_alt_sol": lambda: kenar("alt_sol"), "kenar_alt_sag": lambda: kenar("alt_sag"),
    "yatak_mavi": lambda: yatak(YORGAN_MAVI), "yatak_kirmizi": lambda: yatak(YORGAN_KIRMIZI),
    "yatak_yesil": lambda: yatak(YORGAN_YESIL), "yatak_sari": lambda: yatak(YORGAN_SARI),
    "yatak_mor": lambda: yatak(YORGAN_MOR),
    "masa": lambda: masa(YORGAN_KIRMIZI), "masa_duz": lambda: masa(None), "tabure": tabure,
    "somine": lambda: somine(TAS), "somine_tugla": lambda: somine(TUGLA),
    "kitaplik": kitaplik, "dolap": dolap,
    "pencere_mavi": lambda: pencere(YORGAN_MAVI), "pencere_kirmizi": lambda: pencere(YORGAN_KIRMIZI),
    "pencere_yesil": lambda: pencere(YORGAN_YESIL), "tablo": tablo, "saksi": saksi,
    "hali_kirmizi": lambda: hali(YORGAN_KIRMIZI), "hali_mavi": lambda: hali(YORGAN_MAVI),
    "hali_yesil": lambda: hali(YORGAN_YESIL), "hali_mor": lambda: hali(YORGAN_MOR),
    "paspas": lambda: paspas(zemin_tahta()),
    "tezgah_sol": lambda: tezgah("sol"), "tezgah_orta": lambda: tezgah("orta"), "tezgah_sag": lambda: tezgah("sag"),
    "tezgah_duz": lambda: tezgah("duz"),
    "mal_rafi_1": lambda: mal_rafi(1), "mal_rafi_2": lambda: mal_rafi(2), "mal_rafi_3": lambda: mal_rafi(3),
    "fici": fici, "sandik": sandik, "cuval": cuval,
    "saman_balyasi": saman_balyasi, "yalak": yalak, "bolme": bolme,
    "marangoz_tezgahi": marangoz_tezgahi, "odun_yigini": odun_yigini,
}
SUTUN = 16


def sayfa():
    """Dönen: (görsel, {ad: (karo_x, karo_y, genişlik, yükseklik)})."""
    resimler = [(ad, ciz()) for ad, ciz in PARCALAR.items()]
    yerler, x, y, satir_y = {}, 0, 0, 0
    for ad, im in resimler:
        gk, yk = im.width // 16, im.height // 16
        if x + gk > SUTUN:
            x, y, satir_y = 0, y + satir_y, 0
        yerler[ad] = (x, y, gk, yk)
        x += gk
        satir_y = max(satir_y, yk)
    tum = Image.new("RGBA", (SUTUN * 16, (y + satir_y) * 16), (0, 0, 0, 0))
    for ad, im in resimler:
        tum.paste(im, (yerler[ad][0] * 16, yerler[ad][1] * 16))
    return tum, yerler


def yaz():
    tum, yerler = sayfa()
    tum.save(ASSETS / "cinarkoy_ic.png")
    return tum, yerler


if __name__ == "__main__":
    im, yerler = yaz()
    print(f"Yazıldı: {im.width}x{im.height} piksel, {len(yerler)} parça")
