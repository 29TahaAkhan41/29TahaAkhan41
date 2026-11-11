#!/usr/bin/env python3
"""Çınarköy'ün binalarını sıfırdan, piksel piksel çizer.

Oyunun görsellerinden hiçbir piksel kullanmaz. Çıktı, dört mevsim için birer
karo seti: [CP] Cinarkoy/assets/<mevsim>_cinarkoy_evler.png (kışın çatılar karlı).

    python3 tools/ev_ciz.py

harita_uret.py bu dosyayı içe aktarır; BINALAR listesi her binanın karo
setindeki yerini ve haritaya nasıl yerleşeceğini söyler.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"
MEVSIMLER = ["spring", "summer", "fall", "winter"]

# ---------------------------------------------------------------- renkler ---
# Her palet koyudan açığa 5 ton.
KENAR = (52, 24, 38)
TAS = [(92, 76, 78), (134, 122, 116), (170, 160, 148), (204, 196, 180), (232, 226, 208)]
AHSAP = [(74, 20, 22), (122, 48, 40), (176, 82, 54), (220, 122, 70), (246, 170, 104)]
BAL = [(112, 62, 28), (166, 104, 46), (212, 150, 74), (238, 188, 108), (252, 222, 150)]
SIVA = [(150, 118, 88), (208, 184, 142), (238, 222, 182), (249, 239, 208), (255, 251, 234)]
TUGLA = [(92, 46, 44), (146, 58, 48), (178, 78, 58), (202, 100, 72), (226, 132, 96)]
AHIR = [(80, 16, 24), (130, 28, 34), (176, 46, 44), (206, 74, 60), (232, 112, 92)]
BEYAZ = [(120, 122, 140), (176, 178, 192), (216, 218, 226), (240, 240, 246), (255, 255, 255)]
C_YESIL = [(26, 58, 54), (40, 92, 72), (60, 128, 88), (92, 162, 102), (146, 198, 120)]
C_KIRMIZI = [(68, 16, 26), (118, 32, 38), (166, 52, 48), (202, 86, 62), (232, 130, 90)]
C_ARDUVAZ = [(34, 46, 74), (56, 76, 110), (84, 110, 146), (118, 146, 178), (166, 192, 214)]
C_KIREMIT = [(104, 38, 22), (158, 66, 30), (206, 102, 44), (232, 140, 66), (250, 186, 106)]
C_GRI = [(40, 40, 54), (66, 68, 84), (96, 98, 114), (130, 132, 148), (172, 174, 186)]
CAM = [(60, 110, 160), (105, 183, 213), (160, 216, 234), (222, 250, 255)]
K_YESIL = [(30, 70, 62), (50, 110, 82), (84, 150, 100)]
K_MAVI = [(30, 56, 84), (58, 120, 150), (86, 152, 178)]
K_KIRMIZI = [(84, 18, 26), (160, 48, 46), (204, 86, 66)]
KAR = [(170, 196, 224), (208, 228, 244), (244, 250, 255)]


def zar(*a):
    """Koordinatlardan tekrarlanabilir sözde rastgele sayı (0-1)."""
    n = 0
    for v in a:
        n = (n * 73856093) ^ (int(v) * 19349663 + 83492791)
    n = (n ^ (n >> 13)) * 1274126177
    return ((n ^ (n >> 16)) & 0xFFFF) / 0xFFFF


# ---------------------------------------------------------------- dokular ---
def dok_tas(w, h, P=TAS, tohum=1, sy=8):
    im = Image.new("RGBA", (w, h), P[0] + (255,))
    d = ImageDraw.Draw(im)
    rng = random.Random(tohum)
    y, satir = 0, 0
    while y < h:
        x = -rng.choice((3, 6, 9)) if satir % 2 else 0
        while x < w:
            g = rng.choice((10, 12, 13, 15, 17))
            x0, x1, y1 = x, x + g - 2, y + sy - 2
            ton = rng.choice((1, 2, 2, 2, 3))
            d.rectangle([x0, y, x1, y1], fill=P[ton] + (255,))
            d.line([(x0, y), (x1 - 1, y)], fill=P[ton + 1] + (255,))
            d.line([(x0, y), (x0, y1 - 1)], fill=P[ton + 1] + (255,))
            d.line([(x0 + 1, y1), (x1, y1)], fill=P[ton - 1] + (255,))
            d.line([(x1, y + 1), (x1, y1)], fill=P[ton - 1] + (255,))
            for _ in range(g // 5):
                d.point((rng.randint(x0 + 1, x1 - 1), rng.randint(y + 1, y1 - 1)),
                        fill=P[rng.choice((ton - 1, ton + 1))] + (255,))
            x += g
        y += sy
        satir += 1
    return im


def dok_tugla(w, h, P=TUGLA, tohum=1):
    im = Image.new("RGBA", (w, h), P[0] + (255,))
    px = im.load()
    for y in range(h):
        s = y // 5
        for x in range(w):
            xx = x + (5 if s % 2 else 0)
            if y % 5 == 4 or xx % 10 == 9:
                continue
            ton = 2 + (zar(xx // 10, s, tohum) > 0.75) - (zar(xx // 10, s, tohum + 1) > 0.8)
            if y % 5 == 0:
                ton += 1
            elif y % 5 == 3:
                ton -= 1
            px[x, y] = P[max(1, min(4, ton))] + (255,)
    return im


def dok_tahta_dikey(w, h, P=BAL, tohum=1, gen=7):
    im = Image.new("RGBA", (w, h), P[2] + (255,))
    px = im.load()
    for x in range(w):
        t, i = x // gen, x % gen
        ton = 2 + (zar(t, tohum) > 0.7) - (zar(t, tohum + 5) > 0.8) * 0
        for y in range(h):
            c = ton
            if i == 0:
                c = ton + 1
            elif i == gen - 1:
                c = 0
            elif i == gen - 2:
                c = ton - 1
            elif zar(x, y // 3, tohum) > 0.93:
                c = ton - 1
            elif zar(x, y // 4, tohum + 9) > 0.95:
                c = ton + 1
            px[x, y] = P[max(0, min(4, c))] + (255,)
        if zar(t, tohum + 3) > 0.55:                       # budak / ek yeri
            yy = int(zar(t, tohum + 4) * (h - 4)) + 2
            if 0 < i < gen - 1:
                px[x, yy] = P[1] + (255,)
    return im


def dok_tahta_yatay(w, h, P=BAL, tohum=1, yuk=6):
    return dok_tahta_dikey(h, w, P, tohum, yuk).transpose(Image.TRANSPOSE)


def dok_siva(w, h, P=SIVA, tohum=1):
    im = Image.new("RGBA", (w, h), P[3] + (255,))
    px = im.load()
    for y in range(h):
        for x in range(w):
            z = zar(x, y, tohum)
            if z > 0.965:
                px[x, y] = P[2] + (255,)
            elif z < 0.02:
                px[x, y] = P[4] + (255,)
    d = ImageDraw.Draw(im)
    rng = random.Random(tohum)
    for _ in range(w * h // 900):                          # dökülmüş sıva lekeleri
        x, y = rng.randrange(w), rng.randrange(h)
        d.line([(x, y), (x + rng.randint(2, 5), y)], fill=P[2] + (255,))
        d.line([(x + 1, y + 1), (x + rng.randint(2, 4), y + 1)], fill=P[2] + (255,))
    return im


# ------------------------------------------------------------------ tuval ---
class Tuval:
    def __init__(self, gk, yk, kar=False):
        self.gk, self.yk, self.kar = gk, yk, kar
        self.W, self.H = gk * 16, yk * 16
        self.im = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.px = self.im.load()
        self.cati = {}                    # (x, y) -> çatı derinliği 0-1 (kar için)

    # -- temel --
    def r(self, x0, y0, x1, y1, renk):
        self.d.rectangle([x0, y0, x1, y1], fill=tuple(renk) + (255,))

    def cizgi(self, x0, y0, x1, y1, renk, kal=1):
        self.d.line([(x0, y0), (x1, y1)], fill=tuple(renk) + (255,), width=kal)

    def nokta(self, x, y, renk):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.px[x, y] = tuple(renk) + (255,)

    def karart(self, x, y, k):
        if 0 <= x < self.W and 0 <= y < self.H:
            p = self.px[x, y]
            if p[3]:
                self.px[x, y] = (int(p[0] * k), int(p[1] * k), int(p[2] * k), 255)

    def karart_alan(self, x0, y0, x1, y1, k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.karart(x, y, k)

    def doku(self, dok, cokgen):
        m = Image.new("L", (self.W, self.H), 0)
        ImageDraw.Draw(m).polygon(cokgen, fill=255)
        self.im.paste(dok.crop((0, 0, self.W, self.H)), (0, 0), m)

    def cerceve(self, x0, y0, x1, y1, P, dis=True):
        """Ahşap pervaz: dolu dikdörtgen, ışık solda/üstte, gölge sağda/altta."""
        self.r(x0, y0, x1, y1, P[2])
        self.cizgi(x0, y0, x1, y0, P[3])
        self.cizgi(x0, y0, x0, y1, P[3])
        self.cizgi(x0, y1, x1, y1, P[1])
        self.cizgi(x1, y0, x1, y1, P[1])
        if dis:
            self.d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=P[0] + (255,))

    def kiris(self, x0, y0, x1, y1, P=AHSAP, kal=5):
        """Ahşap kiriş (yatay, dikey ya da çapraz)."""
        self.cizgi(x0, y0, x1, y1, P[0], kal)
        self.cizgi(x0, y0, x1, y1, P[2], kal - 2)
        if x0 == x1:
            self.cizgi(x0 - kal // 2 + 1, y0, x0 - kal // 2 + 1, y1, P[3])
        elif y0 == y1:
            self.cizgi(x0, y0 - kal // 2 + 1, x1, y0 - kal // 2 + 1, P[3])

    # -- çatılar --
    def cati_sacak(self, x0, x1, y0, y1, P, daralma=10, mahya=8, sagda_golge=True):
        """Saçağı izleyene bakan çatı: üstte mahya şeridi, altında kiremit sıraları."""
        sol = lambda y: x0 + daralma - (y - y0) * daralma // (y1 - y0)       # noqa: E731
        sag = lambda y: x1 - daralma + (y - y0) * daralma // (y1 - y0)       # noqa: E731
        satir = 11
        for y in range(y0, y1 + 1):
            s = (y - y0) // satir
            for x in range(sol(y), sag(y) + 1):
                kayma = 0 if s % 2 == 0 else 9
                k, iy, ix = (x + kayma) // 18, (y - y0) % satir, (x + kayma) % 18
                ton = 2 + (zar(k, s, 3) > 0.8) - (zar(k, s, 4) > 0.85)
                if iy <= 1:
                    c = P[ton + 1]
                elif iy == satir - 1 or ix == 17:
                    c = P[0]
                elif ix == 0:
                    c = P[ton + 1]
                elif iy == satir - 2:
                    c = P[ton - 1]
                elif zar(x, y, 5) > 0.97:
                    c = P[ton - 1]
                else:
                    c = P[ton]
                self.nokta(x, y, c)
                self.cati[(x, y)] = 0.25 + 0.75 * (y - y0) / (y1 - y0)
        mx0, mx1 = x0 + daralma + 1, x1 - daralma - 1
        self.r(mx0, y0 - mahya, mx1, y0 - 1, P[3])
        self.r(mx0, y0 - mahya, mx1, y0 - mahya + 1, P[4])
        self.cizgi(mx0, y0 - 1, mx1, y0 - 1, P[1])
        for x in range(mx0 + 9, mx1, 18):
            self.cizgi(x, y0 - mahya + 2, x, y0 - 2, P[2])
        for y in range(y0 - mahya, y0):
            for x in range(mx0, mx1 + 1):
                self.cati[(x, y)] = 0.0
        for y in range(y0, y1 + 1):                        # yan pervazlar
            for k in range(4):
                self.nokta(sol(y) + k, y, (AHSAP[0], AHSAP[3], AHSAP[2], AHSAP[0])[k])
                self.nokta(sag(y) - k, y, (AHSAP[0], AHSAP[2], AHSAP[1], AHSAP[0])[k])
        self.r(x0 - 1, y1 + 1, x1 + 1, y1 + 2, AHSAP[1])   # saçak tahtası
        self.cizgi(x0 - 1, y1 + 1, x1 + 1, y1 + 1, AHSAP[3])
        self.cizgi(x0 - 1, y1 + 3, x1 + 1, y1 + 3, AHSAP[0])
        if sagda_golge:
            self.karart_alan((x0 + x1) // 2 + 6, y0, x1, y1, 0.93)

    def ucgen_y(self, x, xc, yt, yari, yukseklik):
        return yt + abs(x - xc) * yukseklik // yari

    def cati_ucgen(self, xc, yt, yari, yukseklik, D, P, sacak=5):
        """Alınlığı izleyene bakan çatı: iki eğim, geriye doğru D piksel derinlik."""
        tum = yari + sacak
        for x in range(xc - tum, xc + tum + 1):
            yf = self.ucgen_y(x, xc, yt, yari, yukseklik)
            u = abs(x - xc)
            for y in range(yf - D, yf):
                v = y - (yf - D)
                bant, iv = v // 8, v % 8
                iu = (u + (5 if bant % 2 else 0)) % 11
                ton = 2 + (zar(u // 11, bant, 7 + (x < xc)) > 0.8) - (zar(u // 11, bant, 9) > 0.85)
                if v <= 1:
                    c = P[4] if x < xc else P[3]
                elif iv == 7 or iu == 10:
                    c = P[0]
                elif iv == 0:
                    c = P[ton + 1]
                elif iv == 6:
                    c = P[ton - 1]
                elif zar(x, y, 11) > 0.97:
                    c = P[ton - 1]
                else:
                    c = P[ton]
                if x > xc + 1 and v > 1:                   # sağ eğim gölgede
                    c = tuple(int(k * 0.82) for k in c)
                if u <= 1:                                  # mahya
                    c = P[4] if v > 1 else (255, 255, 255)
                elif u == 2:
                    c = P[1]
                self.nokta(x, y, c)
                self.cati[(x, y)] = v / D
            for k, c in enumerate((AHSAP[3], AHSAP[2], AHSAP[1], AHSAP[0])):   # alın tahtası
                self.nokta(x, yf + k, c)
                self.cati[(x, yf + k)] = 1.0

    def ucgen_golge(self, xc, yt, yari, yukseklik, x0, x1, taban):
        """Alın tahtasının altındaki duvara düşen gölge."""
        for x in range(x0, x1 + 1):
            yf = self.ucgen_y(x, xc, yt, yari, yukseklik) + 4
            for y in range(yf, min(yf + 9, taban)):
                self.karart(x, y, 0.74 if y - yf < 5 else 0.87)

    # -- parçalar --
    def pencere(self, x0, y0, g=17, yuk=19, kepenk=K_YESIL, cicek=False, P=AHSAP):
        if kepenk:
            for kx in (x0 - 6, x0 + g + 1):
                self.r(kx, y0, kx + 4, y0 + yuk, kepenk[1])
                self.d.rectangle([kx, y0, kx + 4, y0 + yuk], outline=kepenk[0] + (255,))
                for yy in range(y0 + 3, y0 + yuk - 1, 3):
                    self.cizgi(kx + 1, yy, kx + 3, yy, kepenk[2])
        self.r(x0, y0, x0 + g, y0 + yuk, P[3])
        self.d.rectangle([x0, y0, x0 + g, y0 + yuk], outline=P[0] + (255,))
        self.r(x0 + 2, y0 + 2, x0 + g - 2, y0 + yuk - 2, CAM[1])
        self.d.rectangle([x0 + 2, y0 + 2, x0 + g - 2, y0 + yuk - 2], outline=CAM[0] + (255,))
        self.r(x0 + 3, y0 + 3, x0 + g - 3, y0 + yuk // 2 - 1, CAM[2])
        for i in range(4):
            self.nokta(x0 + 5 + i, y0 + 7 - i, CAM[3])
            self.nokta(x0 + g - 6 + i, y0 + yuk - 5 - i, CAM[3])
        self.r(x0 + g // 2, y0 + 1, x0 + g // 2 + 1, y0 + yuk - 1, P[3])
        self.r(x0 + 1, y0 + yuk // 2, x0 + g - 1, y0 + yuk // 2 + 1, P[3])
        self.cizgi(x0 + 1, y0 + yuk // 2 + 2, x0 + g - 1, y0 + yuk // 2 + 2, P[1])
        self.r(x0 - 1, y0 + yuk + 1, x0 + g + 1, y0 + yuk + 2, P[4])
        self.cizgi(x0 - 1, y0 + yuk + 3, x0 + g + 1, y0 + yuk + 3, P[0])
        if self.kar:
            self.cizgi(x0 - 1, y0 + yuk, x0 + g + 1, y0 + yuk, KAR[2])
            self.cizgi(x0, y0 - 1, x0 + g, y0 - 1, KAR[2])
        if cicek:
            ky = y0 + yuk + 3
            self.r(x0 - 1, ky, x0 + g + 1, ky + 4, P[2])
            self.d.rectangle([x0 - 1, ky, x0 + g + 1, ky + 4], outline=P[0] + (255,))
            self.cizgi(x0, ky + 1, x0 + g, ky + 1, P[3])
            for i, cx in enumerate(range(x0 + 1, x0 + g, 4)):
                if self.kar:
                    self.r(cx - 1, ky - 2, cx + 2, ky - 1, KAR[2])
                    continue
                self.r(cx - 1, ky - 3, cx + 2, ky - 1, (46, 132, 58))
                self.nokta(cx, ky - 4, (84, 176, 72))
                self.nokta(cx + 1, ky - 3, (84, 176, 72))
                renk = [(250, 120, 160), (255, 222, 90), (250, 120, 160), (255, 255, 255)][i % 4]
                self.r(cx, ky - 5, cx + 1, ky - 4, renk)

    def yuvarlak_pencere(self, xc, yc, ycap=6, P=AHSAP):
        self.d.ellipse([xc - ycap - 1, yc - ycap - 1, xc + ycap + 1, yc + ycap + 1], fill=P[0] + (255,))
        self.d.ellipse([xc - ycap, yc - ycap, xc + ycap, yc + ycap], fill=P[3] + (255,))
        self.d.ellipse([xc - ycap + 2, yc - ycap + 2, xc + ycap - 2, yc + ycap - 2],
                       fill=CAM[1] + (255,), outline=CAM[0] + (255,))
        self.cizgi(xc, yc - ycap + 1, xc, yc + ycap - 1, P[3])
        self.cizgi(xc - ycap + 1, yc, xc + ycap - 1, yc, P[3])
        self.nokta(xc - 2, yc - 2, CAM[3])
        self.nokta(xc - 3, yc - 1, CAM[3])

    def kapi(self, x0, y0, taban, g=17, K=K_MAVI, cam=True, P=AHSAP, fener=True):
        x1 = x0 + g
        self.r(x0, y0, x1, taban, P[3])
        self.d.rectangle([x0, y0, x1, taban], outline=P[0] + (255,))
        self.r(x0 + 2, y0 + 2, x1 - 2, taban, K[1])
        self.d.rectangle([x0 + 2, y0 + 2, x1 - 2, taban], outline=K[0] + (255,))
        for xx in (x0 + 6, x0 + 11):
            self.cizgi(xx, y0 + (12 if cam else 4), xx, taban - 1, K[0])
            self.cizgi(xx + 1, y0 + (12 if cam else 4), xx + 1, taban - 1, K[2])
        if cam:
            self.r(x0 + 5, y0 + 4, x1 - 5, y0 + 9, CAM[2])
            self.d.rectangle([x0 + 5, y0 + 4, x1 - 5, y0 + 9], outline=K[0] + (255,))
            self.nokta(x0 + 7, y0 + 6, CAM[3])
            self.nokta(x0 + 8, y0 + 5, CAM[3])
        self.r(x1 - 5, y0 + 19, x1 - 4, y0 + 20, (255, 214, 92))
        self.nokta(x1 - 4, y0 + 21, (176, 120, 40))
        self.esik(x0 - 2, x1 + 2, taban)
        if fener:
            self.fener(x0 + g // 2, y0 - 6)

    def esik(self, x0, x1, taban):
        self.r(x0, taban - 1, x1, taban + 3, TAS[3])
        self.cizgi(x0, taban - 1, x1, taban - 1, KAR[2] if self.kar else TAS[4])
        self.cizgi(x0, taban + 3, x1, taban + 3, TAS[0])

    def fener(self, xc, yc):
        self.r(xc - 1, yc - 3, xc + 2, yc + 2, (255, 226, 120))
        self.d.rectangle([xc - 2, yc - 4, xc + 3, yc + 3], outline=AHSAP[0] + (255,))
        self.nokta(xc, yc - 1, (255, 255, 230))

    def temel(self, x0, x1, y0, y1):
        self.r(x0, y0, x1, y1, TAS[1])
        for x in range(x0, x1, 14):
            self.r(x, y0 + 1, min(x + 12, x1), y1 - 1, TAS[2])
            self.cizgi(x, y0 + 1, min(x + 12, x1), y0 + 1, TAS[3])
        self.cizgi(x0, y0, x1, y0, TAS[0])

    def direk(self, x0, x1, y0, y1, P=AHSAP):
        self.r(x0, y0, x1, y1, P[2])
        self.cizgi(x0, y0, x0, y1, P[0])
        self.cizgi(x1, y0, x1, y1, P[0])
        self.cizgi(x0 + 1, y0, x0 + 1, y1, P[3])
        self.cizgi(x1 - 1, y0, x1 - 1, y1, P[1])

    def baca(self, x0, x1, y0, y1, P=TAS):
        self.r(x0, y0, x1, y1, P[0])
        for i, yy in enumerate(range(y0 + 4, y1, 5)):
            for xx in range(x0 + 1 - (4 if i % 2 else 0), x1, 8):
                a, b = max(xx, x0 + 1), min(xx + 6, x1 - 1)
                if b > a:
                    self.r(a, yy, b, min(yy + 3, y1 - 1), P[2])
                    self.cizgi(a, yy, b, yy, P[3])
        self.karart_alan(x1 - 4, y0 + 4, x1, y1, 0.74)
        self.r(x0 - 1, y0, x1 + 1, y0 + 3, P[1])
        self.cizgi(x0 - 1, y0, x1 + 1, y0, P[3])
        self.r(x0 + 3, y0 + 1, x1 - 3, y0 + 2, (40, 30, 40))
        self.cizgi(x0, y1, x1, y1, KENAR)
        for y in range(y0, y1 + 1):
            for x in range(x0 - 1, x1 + 2):
                self.cati.pop((x, y), None)
        if self.kar:
            self.r(x0 - 1, y0 - 1, x1 + 1, y0, KAR[2])
            self.cizgi(x0, y0 + 1, x1 - 4, y0 + 1, KAR[1])

    # -- son işlemler --
    def kar_ort(self):
        for (x, y), t in self.cati.items():
            if not (0 <= x < self.W and 0 <= y < self.H) or not self.px[x, y][3]:
                continue
            sinir = 0.60 + 0.07 * math.sin(x * 0.45) + 0.05 * math.sin(x * 1.31 + 2)
            if t < sinir:
                self.px[x, y] = KAR[2] + (255,) if zar(x, y, 21) < 0.93 else KAR[1] + (255,)
            elif t < sinir + 0.07:
                self.px[x, y] = KAR[1] + (255,)
            elif t < sinir + 0.10:
                self.px[x, y] = KAR[0] + (255,)

    def bitir(self):
        if self.kar:
            self.kar_ort()
        kaynak = self.im.copy().load()
        for y in range(self.H):
            for x in range(self.W):
                if kaynak[x, y][3] and any(
                        not (0 <= x + dx < self.W and 0 <= y + dy < self.H) or kaynak[x + dx, y + dy][3] == 0
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.px[x, y] = KENAR + (255,)
        return self.im


# ---------------------------------------------------------------- binalar ---
def kulube(kar, duvar="tas", cati=C_YESIL, kapi=K_MAVI, kepenk=K_YESIL, tohum=7):
    """Tek katlı kulübe, saçağı öne bakar. 8x7 karo."""
    t = Tuval(8, 7, kar)
    x0, x1, y0, taban = 8, 119, 60, 107
    dok = dok_tas(t.W, t.H, tohum=tohum) if duvar == "tas" else dok_siva(t.W, t.H, tohum=tohum)
    t.doku(dok, [(x0, y0), (x1, y0), (x1, taban), (x0, taban)])
    t.karart_alan(x0, y0, x1, y0 + 7, 0.72)
    t.karart_alan(x0, y0 + 8, x1, y0 + 10, 0.86)
    t.temel(x0, x1, 100, taban)
    t.direk(x0, x0 + 5, y0, taban)
    t.direk(x1 - 5, x1, y0, taban)
    t.r(x0, y0, x1, y0 + 3, AHSAP[1])
    t.cizgi(x0, y0 + 4, x1, y0 + 4, AHSAP[0])
    t.pencere(24, 72, kepenk=kepenk, cicek=True)
    t.pencere(87, 72, kepenk=kepenk)
    t.kapi(55, 74, taban, K=kapi)
    t.cati_sacak(2, 125, 14, 57, cati)
    t.baca(90, 103, 2, 30)
    return t.bitir()


def ahsap_ev(kar):
    """Dik tahta kaplı, alınlığı öne bakan ev. 7x9 karo."""
    t = Tuval(7, 9, kar)
    xc, yt, yari, yuk, D = 56, 50, 46, 44, 40          # alınlık tepesi (56,50), saçak y=94
    x0, x1, taban = 10, 101, 139
    t.doku(dok_tahta_dikey(t.W, t.H, BAL, 3),
           [(x0, taban), (x0, t.ucgen_y(x0, xc, yt, yari, yuk)), (xc, yt),
            (x1, t.ucgen_y(x1, xc, yt, yari, yuk)), (x1, taban)])
    t.ucgen_golge(xc, yt, yari, yuk, x0, x1, taban)
    t.temel(x0, x1, 132, taban)
    t.direk(x0, x0 + 4, 94, taban, BAL)
    t.direk(x1 - 4, x1, 94, taban, BAL)
    t.kiris(x0, 96, x1, 96, AHSAP, 5)
    t.yuvarlak_pencere(xc, 78)
    t.pencere(20, 106, g=17, yuk=17, kepenk=K_KIRMIZI, cicek=True)
    t.kapi(62, 104, taban, K=K_YESIL)
    t.baca(22, 33, 18, 52)
    t.cati_ucgen(xc, yt, yari, yuk, D, C_KIRMIZI)
    return t.bitir()


def iki_katli(kar):
    """Sıvalı, ahşap çatkılı iki katlı ev. 9x11 karo."""
    t = Tuval(9, 11, kar)
    xc, yt, yari, yuk, D = 72, 46, 60, 50, 42          # saçak y=96
    x0, x1, taban = 12, 131, 171
    t.doku(dok_siva(t.W, t.H, tohum=5),
           [(x0, taban), (x0, t.ucgen_y(x0, xc, yt, yari, yuk)), (xc, yt),
            (x1, t.ucgen_y(x1, xc, yt, yari, yuk)), (x1, taban)])
    t.ucgen_golge(xc, yt, yari, yuk, x0, x1, taban)
    t.temel(x0, x1, 163, taban)
    # çatkı: alınlık içi
    t.kiris(xc, yt + 8, xc, 96, AHSAP)
    t.kiris(xc - 26, 96, xc, 70, AHSAP)
    t.kiris(xc + 26, 96, xc, 70, AHSAP)
    # katlar arası ve üst kiriş
    for yy in (96, 132):
        t.kiris(x0, yy, x1, yy, AHSAP, 5)
    for xx in (x0 + 2, x1 - 2, 44, 100):
        t.kiris(xx, 96, xx, 163, AHSAP)
    t.kiris(14, 131, 42, 99, AHSAP)                    # üst kat çapraz payandalar
    t.kiris(129, 131, 102, 99, AHSAP)
    t.yuvarlak_pencere(xc, 82, 5)
    t.pencere(57, 104, g=13, yuk=19, kepenk=None)      # üst kat
    t.pencere(73, 104, g=13, yuk=19, kepenk=None, cicek=False)
    t.r(56, 126, 88, 129, AHSAP[2])                    # balkon korkuluğu
    t.d.rectangle([55, 125, 89, 130], outline=AHSAP[0] + (255,))
    for xx in range(58, 88, 4):
        t.cizgi(xx, 126, xx, 129, AHSAP[4])
    t.pencere(20, 138, g=17, yuk=17, kepenk=K_MAVI, cicek=True)
    t.pencere(107, 138, g=17, yuk=17, kepenk=K_MAVI, cicek=True)
    t.kapi(63, 138, taban, K=K_KIRMIZI)
    t.baca(104, 117, 14, 56)
    t.cati_ucgen(xc, yt, yari, yuk, D, C_ARDUVAZ)
    return t.bitir()


HARF = {"B": ["110", "101", "110", "101", "110"], "A": ["010", "101", "111", "101", "101"],
        "K": ["101", "110", "100", "110", "101"], "L": ["100", "100", "100", "100", "111"]}


def dukkan(kar):
    """Tuğla dükkân: tenteli vitrin ve tabela. 10x7 karo."""
    t = Tuval(10, 7, kar)
    x0, x1, y0, taban = 8, 151, 60, 107
    t.doku(dok_tugla(t.W, t.H), [(x0, y0), (x1, y0), (x1, taban), (x0, taban)])
    t.karart_alan(x0, y0, x1, y0 + 6, 0.74)
    t.temel(x0, x1, 100, taban)
    t.direk(x0, x0 + 5, y0, taban)
    t.direk(x1 - 5, x1, y0, taban)
    # vitrin
    vx0, vx1, vy0, vy1 = 60, 138, 78, 99
    t.r(vx0, vy0, vx1, vy1, AHSAP[3])
    t.d.rectangle([vx0, vy0, vx1, vy1], outline=AHSAP[0] + (255,))
    t.r(vx0 + 2, vy0 + 2, vx1 - 2, vy1 - 2, CAM[1])
    t.d.rectangle([vx0 + 2, vy0 + 2, vx1 - 2, vy1 - 2], outline=CAM[0] + (255,))
    t.r(vx0 + 3, vy0 + 3, vx1 - 3, vy0 + 9, CAM[2])
    for xx in (vx0 + 26, vx0 + 52):
        t.r(xx, vy0 + 1, xx + 1, vy1 - 1, AHSAP[3])
    for bx in (vx0 + 8, vx0 + 34, vx0 + 60):
        for i in range(5):
            t.nokta(bx + i, vy0 + 9 - i, CAM[3])
    # vitrindeki mallar: sepetler ve kavanozlar
    for i, bx in enumerate(range(vx0 + 6, vx1 - 8, 13)):
        renk = [(214, 72, 60), (240, 190, 70), (110, 170, 70), (214, 72, 60), (150, 100, 190), (240, 190, 70)][i % 6]
        t.r(bx, vy1 - 7, bx + 7, vy1 - 3, BAL[1])
        t.cizgi(bx, vy1 - 7, bx + 7, vy1 - 7, BAL[3])
        for k in range(3):
            t.r(bx + 1 + k * 2, vy1 - 9, bx + 2 + k * 2, vy1 - 8, renk)
    t.r(vx0 - 1, vy1 + 1, vx1 + 1, vy1 + 2, AHSAP[4])
    t.cizgi(vx0 - 1, vy1 + 3, vx1 + 1, vy1 + 3, AHSAP[0])
    # tente
    for x in range(vx0 - 4, vx1 + 5):
        serit = ((x - vx0 + 4) // 6) % 2
        for y in range(66, 79):
            c = (222, 66, 60) if serit else (250, 246, 236)
            if y >= 76:
                c = (160, 40, 44) if serit else (206, 200, 196)
                if y == 78 and (x - vx0 + 4) % 6 in (0, 5):
                    continue
            if y == 66:
                c = (255, 140, 120) if serit else (255, 255, 255)
            t.nokta(x, y, c)
            if kar and y < 70:
                t.nokta(x, y, KAR[2] if y < 69 else KAR[1])
    t.d.line([(vx0 - 5, 65), (vx1 + 5, 65)], fill=AHSAP[0] + (255,))
    t.karart_alan(vx0, 79, vx1, 82, 0.8)
    # kapı ve küçük pencere
    t.kapi(26, 74, taban, K=K_YESIL, fener=False)
    # tabela
    sx0, sy0 = 20, 62
    t.r(sx0, sy0, sx0 + 28, sy0 + 9, BAL[3])
    t.d.rectangle([sx0, sy0, sx0 + 28, sy0 + 9], outline=AHSAP[0] + (255,))
    t.cizgi(sx0 + 1, sy0 + 1, sx0 + 27, sy0 + 1, BAL[4])
    for i, h in enumerate("BAKKAL"):
        for yy, sat in enumerate(HARF[h]):
            for xx, b in enumerate(sat):
                if b == "1":
                    t.nokta(sx0 + 3 + i * 4 + xx, sy0 + 3 + yy, AHSAP[0])
    t.cati_sacak(2, 157, 14, 57, C_KIREMIT)
    t.baca(24, 37, 2, 28)
    return t.bitir()


def ahir(kar):
    """Kırmızı ahır: beyaz pervazlı çift kanatlı kapı ve samanlık kapağı. 8x9 karo."""
    t = Tuval(8, 9, kar)
    xc, yt, yari, yuk, D = 64, 52, 54, 40, 40          # saçak y=92
    x0, x1, taban = 10, 117, 139
    t.doku(dok_tahta_dikey(t.W, t.H, AHIR, 11, gen=6),
           [(x0, taban), (x0, t.ucgen_y(x0, xc, yt, yari, yuk)), (xc, yt),
            (x1, t.ucgen_y(x1, xc, yt, yari, yuk)), (x1, taban)])
    t.ucgen_golge(xc, yt, yari, yuk, x0, x1, taban)
    t.temel(x0, x1, 134, taban)
    t.direk(x0, x0 + 4, 92, taban, BEYAZ)
    t.direk(x1 - 4, x1, 92, taban, BEYAZ)
    t.kiris(x0, 94, x1, 94, BEYAZ, 5)
    # samanlık kapağı
    t.r(54, 68, 74, 88, AHIR[1])
    t.d.rectangle([53, 67, 75, 89], outline=BEYAZ[3] + (255,), width=2)
    t.d.rectangle([52, 66, 76, 90], outline=AHIR[0] + (255,))
    t.cizgi(56, 70, 72, 86, BEYAZ[3], 2)
    t.cizgi(72, 70, 56, 86, BEYAZ[3], 2)
    if not kar:
        for i in range(6):                              # taşan saman
            t.r(55 + i * 3, 86 - (i % 2), 56 + i * 3, 88, (240, 200, 90))
    # çift kanatlı kapı
    dx0, dx1, dy0 = 42, 86, 102
    t.r(dx0, dy0, dx1, taban, AHIR[1])
    for xx in range(dx0 + 3, dx1, 6):
        t.cizgi(xx, dy0, xx, taban, AHIR[0])
    t.d.rectangle([dx0, dy0, dx1, taban], outline=BEYAZ[3] + (255,), width=3)
    t.d.rectangle([dx0 - 1, dy0 - 1, dx1 + 1, taban], outline=AHIR[0] + (255,))
    t.r(xc - 1, dy0, xc, taban, BEYAZ[3])
    for a, b in ((dx0 + 3, xc - 2), (xc + 1, dx1 - 3)):
        t.cizgi(a, dy0 + 3, b, taban - 2, BEYAZ[3], 2)
        t.cizgi(b, dy0 + 3, a, taban - 2, BEYAZ[3], 2)
    t.r(xc - 4, 120, xc - 3, 122, (60, 50, 56))
    t.r(xc + 2, 120, xc + 3, 122, (60, 50, 56))
    t.esik(dx0 - 2, dx1 + 2, taban)
    t.pencere(18, 108, g=13, yuk=13, kepenk=None, P=BEYAZ[:1] + BEYAZ[1:])
    t.pencere(96, 108, g=13, yuk=13, kepenk=None, P=BEYAZ)
    t.cati_ucgen(xc, yt, yari, yuk, D, C_GRI)
    return t.bitir()


def kuyu(kar):
    """Taş kuyu, küçük çatılı. 3x4 karo."""
    t = Tuval(3, 4, kar)
    xc = 24
    t.d.ellipse([6, 34, 41, 50], fill=TAS[3] + (255,), outline=TAS[0] + (255,))   # ağız
    t.d.ellipse([10, 37, 37, 47], fill=(38, 70, 110, 255), outline=TAS[0] + (255,))
    t.d.ellipse([14, 40, 30, 45], fill=(60, 110, 160, 255))
    dok = dok_tas(t.W, t.H, tohum=4, sy=6)
    t.doku(dok, [(6, 43), (41, 43), (41, 58), (36, 62), (11, 62), (6, 58)])
    t.d.arc([6, 34, 41, 50], 0, 180, fill=TAS[4] + (255,))
    t.karart_alan(32, 44, 41, 62, 0.8)
    t.direk(8, 11, 16, 43)
    t.direk(36, 39, 16, 43)
    t.kiris(10, 24, 38, 24, AHSAP, 3)                  # makara mili
    t.cizgi(xc, 25, xc, 36, (226, 210, 170))           # ip
    t.r(xc - 3, 36, xc + 3, 41, BAL[2])                # kova
    t.d.rectangle([xc - 3, 36, xc + 3, 41], outline=AHSAP[0] + (255,))
    t.cizgi(xc - 2, 38, xc + 2, 38, C_GRI[3])
    t.cati_ucgen(xc, 6, 20, 10, 6, C_KIRMIZI, sacak=2)
    return t.bitir()


# (ad, çizen işlev, üstten kaç karo sırası oyuncunun önünde çizilir, kapı sütunları)
BINALAR = [
    ("tas_kulube", lambda kar: kulube(kar), 3, (3, 4)),
    ("siva_kulube", lambda kar: kulube(kar, "siva", C_KIREMIT, K_KIRMIZI, K_MAVI, tohum=9), 3, (3, 4)),
    ("ahsap_ev", ahsap_ev, 5, (4,)),
    ("iki_katli", iki_katli, 6, (4,)),
    ("dukkan", dukkan, 3, (1, 2)),
    ("ahir", ahir, 5, (3, 4)),
    ("kuyu", kuyu, 2, ()),
]
SAYFA_SUTUN = 16


def sayfa(kar=False):
    """Bütün binaları tek karo setine dizer.
    Dönen: (görsel, {ad: (karo_x, karo_y, genişlik, yükseklik, ön_sıra, kapı_sütunları)})."""
    resimler = [(ad, ciz(kar), on, kapi) for ad, ciz, on, kapi in BINALAR]
    yerler, x, y, satir_y = {}, 0, 0, 0
    for ad, im, on, kapi in resimler:
        gk, yk = im.width // 16, im.height // 16
        if x + gk > SAYFA_SUTUN:
            x, y, satir_y = 0, y + satir_y, 0
        yerler[ad] = (x, y, gk, yk, on, kapi)
        x += gk
        satir_y = max(satir_y, yk)
    tum = Image.new("RGBA", (SAYFA_SUTUN * 16, (y + satir_y) * 16), (0, 0, 0, 0))
    for ad, im, on, kapi in resimler:
        tum.paste(im, (yerler[ad][0] * 16, yerler[ad][1] * 16))
    return tum, yerler


def yaz():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for mevsim in MEVSIMLER:
        sayfa(kar=mevsim == "winter")[0].save(ASSETS / f"{mevsim}_cinarkoy_evler.png")
    return sayfa()


if __name__ == "__main__":
    im, yerler = yaz()
    print(f"Yazıldı: {im.width}x{im.height} piksel, {len(yerler)} bina")
