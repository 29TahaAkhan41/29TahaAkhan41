#!/usr/bin/env python3
"""Sıfırdan çizilmiş özgün ev: taş duvarlı, yeşil çatılı kulübe.

Oyunun görsellerinden hiçbir piksel kullanmaz; yalnızca piksel piksel çizer.
Çıktı: [CP] Cinarkoy/assets/cinarkoy_kulube.png (8x7 karo, 128x112 piksel)

    python3 tools/ev_ciz.py
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "[CP] Cinarkoy" / "assets" / "cinarkoy_kulube.png"
W, H = 128, 112
rng = random.Random(7)

KENAR = (52, 24, 38, 255)                      # dış hat
CATI = [(26, 58, 54), (40, 92, 72), (60, 128, 88), (92, 162, 102), (146, 198, 120)]
TAS = [(92, 76, 78), (134, 122, 116), (170, 160, 148), (204, 196, 180), (232, 226, 208)]
AHSAP = [(74, 20, 22), (122, 48, 40), (176, 82, 54), (220, 122, 70), (246, 170, 104)]
CAM = [(60, 110, 160), (105, 183, 213), (160, 216, 234), (222, 250, 255)]
KEPENK = [(30, 70, 62), (50, 110, 82), (84, 150, 100)]

im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
px = im.load()


def r(x0, y0, x1, y1, renk):
    d.rectangle([x0, y0, x1, y1], fill=renk + (255,) if len(renk) == 3 else renk)


def karart(x0, y0, x1, y1, k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = px[x, y]
            if p[3]:
                px[x, y] = (int(p[0] * k), int(p[1] * k), int(p[2] * k), 255)


# ----------------------------------------------------------------- duvar ---
DX0, DX1, DY0, DY1 = 8, 119, 60, 107
r(DX0, DY0, DX1, DY1, TAS[0])
y = DY0
satir = 0
while y <= DY1:
    x = DX0 - rng.choice((0, 5, 9)) if satir % 2 else DX0
    while x <= DX1:
        g = rng.choice((10, 12, 13, 15, 17))
        x0, x1 = max(x, DX0), min(x + g - 2, DX1)
        y1 = min(y + 6, DY1)
        if x1 > x0:
            ton = rng.choice((1, 2, 2, 2, 3))
            r(x0, y, x1, y1, TAS[ton])
            d.line([(x0, y), (x1 - 1, y)], fill=TAS[ton + 1] + (255,))          # üst ışık
            d.line([(x0, y), (x0, y1 - 1)], fill=TAS[ton + 1] + (255,))
            d.line([(x0 + 1, y1), (x1, y1)], fill=TAS[ton - 1] + (255,))        # alt gölge
            d.line([(x1, y + 1), (x1, y1)], fill=TAS[ton - 1] + (255,))
            for _ in range(g // 5):
                px[rng.randint(x0 + 1, x1 - 1), rng.randint(y + 1, y1 - 1)] = TAS[rng.choice((ton - 1, ton + 1))] + (255,)
        x += g
    y += 8
    satir += 1
karart(DX0, DY0, DX1, DY0 + 7, 0.72)            # saçak gölgesi
karart(DX0, DY0 + 8, DX1, DY0 + 10, 0.86)
r(DX0, 100, DX1, DY1, TAS[1])                   # temel
for x in range(DX0, DX1, 14):
    r(x, 101, min(x + 12, DX1), 106, TAS[2])
    d.line([(x, 101), (min(x + 12, DX1), 101)], fill=TAS[3] + (255,))
d.line([(DX0, 100), (DX1, 100)], fill=TAS[0] + (255,))


def direk(x0, x1, y0, y1):
    r(x0, y0, x1, y1, AHSAP[2])
    d.line([(x0, y0), (x0, y1)], fill=AHSAP[0] + (255,))
    d.line([(x1, y0), (x1, y1)], fill=AHSAP[0] + (255,))
    d.line([(x0 + 1, y0), (x0 + 1, y1)], fill=AHSAP[3] + (255,))
    d.line([(x1 - 1, y0), (x1 - 1, y1)], fill=AHSAP[1] + (255,))


direk(DX0, DX0 + 5, DY0, DY1)                   # köşe direkleri
direk(DX1 - 5, DX1, DY0, DY1)
r(DX0, DY0, DX1, DY0 + 3, AHSAP[1])             # üst kiriş
d.line([(DX0, DY0 + 4), (DX1, DY0 + 4)], fill=AHSAP[0] + (255,))


# -------------------------------------------------------------- pencere ---
def pencere(x0, y0, cicek=False):
    g, yuk = 17, 19
    for kx in (x0 - 6, x0 + g + 1):             # kepenkler
        r(kx, y0, kx + 4, y0 + yuk, KEPENK[1])
        d.rectangle([kx, y0, kx + 4, y0 + yuk], outline=KEPENK[0] + (255,))
        for yy in range(y0 + 3, y0 + yuk - 1, 3):
            d.line([(kx + 1, yy), (kx + 3, yy)], fill=KEPENK[2] + (255,))
    r(x0, y0, x0 + g, y0 + yuk, AHSAP[3])       # çerçeve
    d.rectangle([x0, y0, x0 + g, y0 + yuk], outline=AHSAP[0] + (255,))
    r(x0 + 2, y0 + 2, x0 + g - 2, y0 + yuk - 2, CAM[1])
    d.rectangle([x0 + 2, y0 + 2, x0 + g - 2, y0 + yuk - 2], outline=CAM[0] + (255,))
    r(x0 + 3, y0 + 3, x0 + g - 3, y0 + 8, CAM[2])
    for i in range(4):                          # cam parıltısı
        px[x0 + 5 + i, y0 + 7 - i] = CAM[3] + (255,)
        px[x0 + 11 + i, y0 + 14 - i] = CAM[3] + (255,)
    r(x0 + g // 2, y0 + 1, x0 + g // 2 + 1, y0 + yuk - 1, AHSAP[3])   # kayıtlar
    r(x0 + 1, y0 + 9, x0 + g - 1, y0 + 10, AHSAP[3])
    d.line([(x0 + 1, y0 + 11), (x0 + g - 1, y0 + 11)], fill=AHSAP[1] + (255,))
    r(x0 - 1, y0 + yuk + 1, x0 + g + 1, y0 + yuk + 2, AHSAP[4])       # denizlik
    d.line([(x0 - 1, y0 + yuk + 3), (x0 + g + 1, y0 + yuk + 3)], fill=AHSAP[0] + (255,))
    if cicek:
        r(x0 - 1, y0 + yuk + 3, x0 + g + 1, y0 + yuk + 7, AHSAP[2])
        d.rectangle([x0 - 1, y0 + yuk + 3, x0 + g + 1, y0 + yuk + 7], outline=AHSAP[0] + (255,))
        d.line([(x0, y0 + yuk + 4), (x0 + g, y0 + yuk + 4)], fill=AHSAP[3] + (255,))
        for i, cx in enumerate(range(x0 + 1, x0 + g, 4)):
            r(cx - 1, y0 + yuk, cx + 2, y0 + yuk + 2, (46, 132, 58))
            px[cx, y0 + yuk - 1] = (84, 176, 72, 255)
            px[cx + 1, y0 + yuk] = (84, 176, 72, 255)
            renk = [(250, 120, 160), (255, 222, 90), (250, 120, 160), (255, 255, 255)][i % 4]
            r(cx, y0 + yuk - 2, cx + 1, y0 + yuk - 1, renk)


pencere(24, 72, cicek=True)
pencere(87, 72)

# ------------------------------------------------------------------ kapı ---
KX0, KX1, KY0 = 55, 72, 74
r(KX0, KY0, KX1, DY1, AHSAP[3])
d.rectangle([KX0, KY0, KX1, DY1], outline=AHSAP[0] + (255,))
r(KX0 + 2, KY0 + 2, KX1 - 2, DY1, (58, 120, 150))            # kapı kanadı (mavi)
d.rectangle([KX0 + 2, KY0 + 2, KX1 - 2, DY1], outline=(30, 56, 84, 255))
for xx in (KX0 + 6, KX0 + 11):
    d.line([(xx, KY0 + 12), (xx, DY1 - 1)], fill=(40, 86, 116, 255))
    d.line([(xx + 1, KY0 + 12), (xx + 1, DY1 - 1)], fill=(86, 152, 178, 255))
r(KX0 + 5, KY0 + 4, KX1 - 5, KY0 + 9, CAM[2])                # kapı camı
d.rectangle([KX0 + 5, KY0 + 4, KX1 - 5, KY0 + 9], outline=(30, 56, 84, 255))
px[KX0 + 7, KY0 + 6] = CAM[3] + (255,)
px[KX0 + 8, KY0 + 5] = CAM[3] + (255,)
r(KX1 - 5, KY0 + 19, KX1 - 4, KY0 + 20, (255, 214, 92))      # tokmak
px[KX1 - 4, KY0 + 21] = (176, 120, 40, 255)
r(KX0 - 2, DY1 - 1, KX1 + 2, DY1 + 3, TAS[3])                # eşik
d.line([(KX0 - 2, DY1 - 1), (KX1 + 2, DY1 - 1)], fill=TAS[4] + (255,))
d.line([(KX0 - 2, DY1 + 3), (KX1 + 2, DY1 + 3)], fill=TAS[0] + (255,))
# kapı üstü fener
r(KX0 + 7, KY0 - 9, KX0 + 10, KY0 - 4, (255, 226, 120))
d.rectangle([KX0 + 6, KY0 - 10, KX0 + 11, KY0 - 3], outline=AHSAP[0] + (255,))
px[KX0 + 8, KY0 - 7] = (255, 255, 230, 255)

# ------------------------------------------------------------------ çatı ---
CY0, CY1 = 14, 57                                # ön eğim
SOL = lambda yy: 12 - (yy - CY0) * 11 // (CY1 - CY0)          # noqa: E731
SAG = lambda yy: 115 + (yy - CY0) * 11 // (CY1 - CY0)         # noqa: E731
SATIR = 11
for yy in range(CY0, CY1 + 1):
    s = (yy - CY0) // SATIR
    for xx in range(SOL(yy), SAG(yy) + 1):
        kayma = 0 if s % 2 == 0 else 9
        kiremit = (xx + kayma) // 18
        ton = 2 + ((kiremit * 7 + s * 3) % 5 == 0) - ((kiremit * 5 + s) % 7 == 0)
        iy, ix = (yy - CY0) % SATIR, (xx + kayma) % 18
        renk = CATI[ton]
        if iy <= 1:
            renk = CATI[ton + 1]                 # üst kenar ışığı
        if iy == SATIR - 1 or ix == 17:
            renk = CATI[0]                       # kiremit arası çizgi
        elif ix == 0 and iy > 1:
            renk = CATI[ton + 1]
        elif iy == SATIR - 2:
            renk = CATI[ton - 1]
        px[xx, yy] = renk + (255,)
for _ in range(60):                              # benekler
    yy = rng.randint(CY0 + 2, CY1 - 3)
    xx = rng.randint(SOL(yy) + 2, SAG(yy) - 2)
    if px[xx, yy][:3] == CATI[2]:
        px[xx, yy] = rng.choice((CATI[1], CATI[3])) + (255,)
r(13, 6, 114, 13, CATI[3])                       # mahya (çatının üst yüzü)
d.line([(13, 6), (114, 6)], fill=CATI[4] + (255,))
d.line([(13, 7), (114, 7)], fill=CATI[4] + (255,))
d.line([(13, 13), (114, 13)], fill=CATI[1] + (255,))
for xx in range(22, 114, 18):
    d.line([(xx, 8), (xx, 12)], fill=CATI[2] + (255,))
for yy in range(CY0, CY1 + 1):                   # yan pervazlar
    for k, renk in enumerate((AHSAP[0], AHSAP[3], AHSAP[2], AHSAP[0])):
        px[SOL(yy) + k, yy] = renk + (255,)
        px[SAG(yy) - k, yy] = (AHSAP[0], AHSAP[2], AHSAP[1], AHSAP[0])[k] + (255,)
r(1, CY1 + 1, 126, CY1 + 2, AHSAP[1])            # saçak tahtası
d.line([(1, CY1 + 1), (126, CY1 + 1)], fill=AHSAP[3] + (255,))
d.line([(1, CY1 + 3), (126, CY1 + 3)], fill=AHSAP[0] + (255,))
karart(70, CY0, 126, CY1, 0.93)                  # sağ yarı biraz gölgede

# ------------------------------------------------------------------ baca ---
BX0, BX1, BY0, BY1 = 90, 103, 2, 30
r(BX0, BY0, BX1, BY1, TAS[0])
for i, yy in enumerate(range(BY0 + 4, BY1, 5)):
    for xx in range(BX0 + 1 - (4 if i % 2 else 0), BX1, 8):
        x0, x1 = max(xx, BX0 + 1), min(xx + 6, BX1 - 1)
        if x1 > x0:
            r(x0, yy, x1, yy + 3, TAS[2])
            d.line([(x0, yy), (x1, yy)], fill=TAS[3] + (255,))
karart(BX1 - 4, BY0 + 4, BX1, BY1, 0.74)
r(BX0 - 1, BY0, BX1 + 1, BY0 + 3, TAS[1])        # baca şapkası
d.line([(BX0 - 1, BY0), (BX1 + 1, BY0)], fill=TAS[3] + (255,))
r(BX0 + 3, BY0 + 1, BX1 - 3, BY0 + 2, (40, 30, 40))
d.line([(BX0, BY1), (BX1, BY1)], fill=CATI[0] + (255,))

# -------------------------------------------------------------- dış hat ---
kaynak = im.copy().load()
for y in range(H):
    for x in range(W):
        if kaynak[x, y][3] and any(
                not (0 <= x + dx < W and 0 <= y + dy < H) or kaynak[x + dx, y + dy][3] == 0
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = KENAR

if __name__ == "__main__":
    im.save(CIKTI)
    print("Yazıldı:", CIKTI)
