#!/usr/bin/env python3
"""Çınarköy'ün köylülerini sıfırdan çizer: yürüme sprite'ları ve portreler.

Oyunun karakter görsellerinden hiçbir piksel kullanmaz; yalnızca aynı ölçülere
uyar, böylece oyun onları kendi karakterleri gibi okur:

  sprite  : 64x128 piksel, 16x32'lik kareler; satırlar aşağı / sağ / yukarı / sol
            bakış, her satırda 4 yürüme karesi
  portre  : 128x192 piksel, 64x64'lük 6 ifade: nötr, mutlu, üzgün, şaşkın,
            sevgi dolu, kızgın (diyaloglardaki $h $s $u $l $a sırasıyla)

Çıktı: [CP] Cinarkoy/assets/karakterler/<Ad>.png ve assets/portreler/<Ad>.png

    python3 tools/karakter_ciz.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"

# Paletler: (koyu, orta, açık)
TEN_ACIK = [(196, 120, 96), (246, 190, 150), (255, 222, 190)]
TEN_BUGDAY = [(160, 92, 66), (222, 158, 112), (246, 198, 150)]
TEN_SOLUK = [(190, 124, 116), (244, 200, 176), (255, 230, 212)]
SAC_KAHVE = [(58, 28, 20), (110, 60, 30), (160, 100, 50)]
SAC_SIYAH = [(22, 20, 34), (52, 46, 66), (92, 86, 112)]
SAC_KIZIL = [(110, 34, 16), (190, 78, 28), (240, 138, 60)]
SAC_GRI = [(110, 106, 120), (176, 174, 186), (232, 232, 240)]
KREM = [(150, 130, 110), (236, 226, 204), (255, 252, 240)]
YESIL = [(28, 80, 50), (56, 136, 78), (110, 188, 110)]
MAVI = [(34, 60, 110), (64, 106, 170), (118, 160, 216)]
KIRMIZI = [(110, 24, 30), (190, 54, 52), (236, 110, 96)]
MOR = [(64, 30, 70), (118, 62, 124), (170, 112, 176)]
LILA = [(120, 90, 150), (186, 160, 214), (228, 212, 244)]
KAHVE = [(64, 36, 24), (122, 76, 44), (176, 122, 76)]
GRI = [(56, 58, 72), (104, 108, 124), (156, 160, 176)]
SARI = [(170, 110, 30), (242, 196, 70), (255, 236, 150)]
SIYAH_AYK = [(20, 14, 22), (58, 44, 52), (96, 80, 88)]

KOYLULER = {
    "Halil": dict(tip="yetiskin", ten=TEN_BUGDAY, sac=SAC_KAHVE, stil="kisa", perc="yana", biyik=True,
                  ust=KREM, alt=KAHVE, ayk=SIYAH_AYK, onluk=YESIL, goz=(70, 44, 30)),
    "Nazife": dict(tip="yasli", ten=TEN_SOLUK, sac=SAC_GRI, stil="basortu", perc="duz", ortu=LILA,
                   ust=MOR, alt=MOR, ayk=SIYAH_AYK, etek=True, goz=(70, 90, 110)),
    "Kerem": dict(tip="yetiskin", ten=TEN_BUGDAY, sac=SAC_SIYAH, stil="kisa", perc="duz", ust=KIRMIZI,
                  alt=MAVI, ayk=KAHVE, askili=True, kisa_kol=True, goz=(50, 40, 34)),
    "Zeynep": dict(tip="yetiskin", ten=TEN_ACIK, sac=SAC_KIZIL, stil="atkuyrugu", perc="yana", ust=YESIL,
                   alt=GRI, ayk=KAHVE, yelek=KAHVE, goz=(40, 120, 90), kadin=True),
    "Elif": dict(tip="cocuk", ten=TEN_ACIK, sac=SAC_KAHVE, stil="kut", perc="duz", ust=SARI, alt=SARI,
                 ayk=KIRMIZI, etek=True, goz=(60, 50, 40), kadin=True),
}


def koyu(c, k=0.55):
    return tuple(int(v * k) for v in c)


# =================================================================== sprite ===
ON = [(5, 10), (4, 11), (3, 12), (3, 12), (3, 12), (3, 12), (3, 12), (3, 12), (4, 11), (5, 10)]
YAN = [(5, 10), (4, 11), (3, 12), (3, 12), (3, 12), (3, 12), (3, 13), (3, 12), (4, 11), (5, 10)]


def olculer(tip):
    """(baş üst satırı, gövde üstü, gövde altı, kol dış sol, kol dış sağ, bacak sol, bacak sağ)"""
    if tip == "cocuk":
        return 10, 20, 25, 3, 12, 5, 10
    if tip == "yasli":
        return 5, 16, 22, 2, 13, 4, 11
    return 4, 15, 22, 2, 13, 4, 11


def sac_hucreleri(k, yon):
    """Saç (ya da örtü/şapka) hücreleri: {(x, y): 'sac' | 'ortu' | 'siperlik'}"""
    H0 = olculer(k["tip"])[0]
    stil, perc = k["stil"], k.get("perc", "duz")
    h = {}

    def satir(y, x0, x1, tur="sac"):
        for x in range(x0, x1 + 1):
            h[(x, y)] = tur

    tur = "ortu" if stil == "basortu" else "sac"
    yan_boy = {"kisa": 5, "kut": 8, "uzun": 13, "atkuyrugu": 5, "topuz": 5, "basortu": 9, "kasket": 5}[stil]
    if yon == "on":
        satir(H0 - 2, 5, 10, tur)
        satir(H0 - 1, 3, 12, tur)
        for y in range(H0, H0 + 3):
            satir(y, 2, 13, tur)
        if perc == "yana":
            satir(H0 + 3, 2, 7, tur)
        elif perc == "orta":
            for x in (7, 8):
                h.pop((x, H0 + 2), None)
        for y in range(H0 + 3, H0 + yan_boy + 1):
            satir(y, 2, 3, tur)
            satir(y, 12, 13, tur)
        if stil == "basortu":
            satir(H0 + 10, 5, 10, tur)
            satir(H0 + 11, 6, 9, tur)
        if stil == "topuz":
            for y, (a, b) in zip(range(H0 - 5, H0 - 1), ((7, 8), (6, 9), (6, 9), (6, 9))):
                satir(y, a, b)
    elif yon == "arka":
        satir(H0 - 2, 5, 10, tur)
        satir(H0 - 1, 3, 12, tur)
        for y in range(H0, H0 + 8):
            satir(y, 2, 13, tur)
        satir(H0 + 8, 3, 12, tur)
        if stil in ("uzun", "kut"):
            for y in range(H0 + 9, H0 + (15 if stil == "uzun" else 10)):
                satir(y, 3, 12)
        elif stil == "atkuyrugu":
            for y in range(H0 + 9, H0 + 16):
                satir(y, 6, 9)
        elif stil == "basortu":
            for y, (a, b) in zip(range(H0 + 9, H0 + 15), ((2, 13), (3, 12), (4, 11), (5, 10), (6, 9), (7, 8))):
                satir(y, a, b, tur)
        elif stil == "topuz":
            for y, (a, b) in zip(range(H0 - 5, H0 - 1), ((7, 8), (6, 9), (6, 9), (6, 9))):
                satir(y, a, b)
    else:                                              # yan (sağa bakar)
        satir(H0 - 2, 5, 10, tur)
        satir(H0 - 1, 3, 12, tur)
        for y in range(H0, H0 + 3):
            satir(y, 2, 12, tur)
        arka_boy = {"kisa": 7, "kut": 9, "uzun": 15, "atkuyrugu": 7, "topuz": 7, "basortu": 12, "kasket": 7}[stil]
        for y in range(H0 + 3, H0 + arka_boy + 1):
            satir(y, 2, 7 if stil == "basortu" else 6, tur)
        if stil == "basortu":
            satir(H0 + 10, 6, 9, tur)
        if stil == "atkuyrugu":
            for y, (a, b) in zip(range(H0 + 2, H0 + 11), ((1, 2), (0, 2), (0, 2), (0, 2), (0, 1), (0, 1), (0, 1), (1, 1), (1, 1))):
                satir(y, a, b)
        if stil == "topuz":
            for y, (a, b) in zip(range(H0 - 1, H0 + 4), ((1, 2), (0, 3), (0, 3), (0, 3), (1, 2))):
                satir(y, a, b)
    return h


def kare(k, yon, no):
    """Tek bir 16x32 yürüme karesi. yon: on / yan / arka; no: 0-3."""
    H0, T0, TB, xl, xr, lx0, lx1 = olculer(k["tip"])
    L0 = TB + 1
    adim = no in (1, 3)
    kay = 1 if adim else 0                             # adım atarken gövde 1 piksel iner
    p, ic = {}, set()                                  # piksel renkleri, iç çizgiler

    def koy(x, y, c):
        if 0 <= x < 16 and 0 <= y < 32:
            p[(x, y)] = c

    def serit(y, x0, x1, c):
        for x in range(x0, x1 + 1):
            koy(x, y, c)

    ten, ust, alt, ayk = k["ten"], k["ust"], k["alt"], k["ayk"]
    etek = k.get("etek")

    # ---- bacaklar ----
    if yon in ("on", "arka"):
        orta = (lx0 + lx1) // 2
        for taraf, (a, b) in enumerate(((lx0, orta), (orta + 1, lx1))):
            kalkik = adim and ((no == 1) == (taraf == 0))
            alt_y = 29 if kalkik else 31
            for y in range(L0, alt_y - 1):
                if etek:
                    serit(y, a + 1, b - 1, ten[1])
                else:
                    serit(y, a, b, alt[1])
            serit(alt_y - 1, a, b, ayk[1])
            serit(alt_y, a, b, ayk[0])
            if not etek:
                for y in range(L0 + 3, alt_y - 1):
                    ic.add((orta, y))
        if etek:
            for i, y in enumerate(range(L0 + kay, L0 + kay + 6)):
                serit(y, lx0 - (1 if i else 0), lx1 + (1 if i else 0), alt[1])
                if i == 5:
                    serit(y, lx0 - 1, lx1 + 1, alt[0])
    else:
        if not adim:
            for y in range(L0, 30):
                if etek:
                    serit(y, 6, 8, ten[1])
                else:
                    serit(y, 5, 10, alt[1])
            serit(30, 5, 11, ayk[1])
            serit(31, 5, 11, ayk[0])
        else:
            diz = min(L0 + 4, 28)
            for y in range(L0, diz):
                serit(y, 5, 10, ten[1] if etek else alt[1])
            for y in range(diz, 29):                   # arka bacak
                serit(y, 3, 6, ten[1] if etek else alt[0])
            serit(29, 2, 6, ayk[1])
            serit(30, 2, 6, ayk[0])
            for y in range(diz, 30):                   # ön bacak
                serit(y, 8, 11, ten[1] if etek else alt[1])
            serit(30, 8, 12, ayk[1])
            serit(31, 8, 12, ayk[0])
        if etek:
            for i, y in enumerate(range(L0 + kay, L0 + kay + 6)):
                serit(y, 4, 11, alt[0] if i == 5 else alt[1])

    # ---- gövde ----
    def govde_y(y):
        return y + kay

    if yon in ("on", "arka"):
        for y in range(T0, TB + 1):
            d = 2 if y == T0 else 1 if y == T0 + 1 else 0
            serit(govde_y(y), xl + d, xr - d, ust[1])
        if k.get("cizgili"):
            for y in range(T0 + 1, TB + 1, 2):
                serit(govde_y(y), xl + 3, xr - 3, ust[2])
        if k.get("yelek"):
            ye = k["yelek"]
            for y in range(T0 + 1, TB + 1):
                if yon == "arka":
                    serit(govde_y(y), xl + 3, xr - 3, ye[1])
                else:
                    serit(govde_y(y), xl + 3, 6, ye[1])
                    serit(govde_y(y), 9, xr - 3, ye[1])
        if k.get("askili"):
            for y in range(T0 + 3, TB + 1):
                serit(govde_y(y), xl + 3, xr - 3, alt[1])
            for y in range(T0, T0 + 3):
                koy(5, govde_y(y), alt[1])
                koy(10, govde_y(y), alt[1])
            if yon == "on":
                koy(5, govde_y(T0 + 3), SARI[1])
                koy(10, govde_y(T0 + 3), SARI[1])
        if k.get("onluk") and yon == "on":
            on = k["onluk"]
            for y in range(T0 + 2, TB + 1):
                serit(govde_y(y), 6, 9, on[1])
            for y in range(TB + 1, TB + 4):
                serit(govde_y(y), 5, 10, on[1])
            serit(govde_y(TB + 4), 5, 10, on[0])
            koy(6, govde_y(T0 + 1), on[1])
            koy(9, govde_y(T0 + 1), on[1])
        if k.get("onluk") and yon == "arka":
            serit(govde_y(TB - 2), xl + 3, xr - 3, k["onluk"][1])
        for y in range(T0 + 3, TB + 1):                # kol çizgileri
            ic.add((xl + 2, govde_y(y)))
            ic.add((xr - 2, govde_y(y)))
        kol_ust = T0 + 4 if k.get("kisa_kol") else TB - 1
        for y in range(kol_ust, TB + 1):               # kollar / eller
            for x in (xl, xl + 1, xr - 1, xr):
                koy(x, govde_y(y), ten[1])
        if yon == "on":
            koy(7, govde_y(T0), ten[1])
            koy(8, govde_y(T0), ten[1])
            koy(xl + 3, govde_y(T0 + 2), ust[2])
    else:
        salin = (1 if no == 1 else -1 if no == 3 else 0)
        for y in range(T0, TB + 1):
            d = 1 if y == T0 else 0
            serit(govde_y(y), 4 + d, 11 - d, ust[1])
        if k.get("yelek"):
            for y in range(T0 + 1, TB + 1):
                serit(govde_y(y), 4, 11, k["yelek"][1])
        if k.get("askili"):
            for y in range(T0 + 3, TB + 1):
                serit(govde_y(y), 4, 11, alt[1])
        if k.get("onluk"):
            for y in range(T0 + 2, min(TB + 4, 29)):
                serit(govde_y(y), 10, 11, k["onluk"][1])
        kol_ust = T0 + 4 if k.get("kisa_kol") else TB - 1
        for y in range(T0 + 2, TB + 1):                # kol
            c = ten[1] if y >= kol_ust else ust[1]
            koy(7 + salin, govde_y(y), c)
            koy(8 + salin, govde_y(y), c)
            if y < TB:
                ic.add((6 + salin, govde_y(y)))
                ic.add((9 + salin, govde_y(y)))

    # ---- baş ----
    h0 = H0 + kay
    tablo = YAN if yon == "yan" else ON
    for i, (a, b) in enumerate(tablo):
        serit(h0 + i, a, b, ten[1])
    serit(h0 + 10, 6, 9, ten[0] if yon != "arka" else ten[1])
    goz, sac = k["goz"], k["sac"]
    if yon == "on":
        for gy in (h0 + 5, h0 + 6):
            koy(5, gy, (255, 255, 255))
            koy(10, gy, (255, 255, 255))
            koy(6, gy, goz if gy == h0 + 5 else koyu(goz, 0.5))
            koy(9, gy, goz if gy == h0 + 5 else koyu(goz, 0.5))
        koy(4, h0 + 7, ten[0])
        koy(11, h0 + 7, ten[0])
        koy(7, h0 + 8, ten[0])
        koy(8, h0 + 8, ten[0])
        koy(4, h0 + 3, ten[2])
        if k.get("kadin") or k["tip"] == "cocuk":
            koy(5, h0 + 7, (250, 150, 140))
            koy(10, h0 + 7, (250, 150, 140))
        if k.get("biyik"):
            serit(h0 + 7, 5, 10, sac[1])
            koy(5, h0 + 8, sac[1])
            koy(10, h0 + 8, sac[1])
    elif yon == "yan":
        for gy in (h0 + 5, h0 + 6):
            koy(10, gy, (255, 255, 255))
            koy(11, gy, goz if gy == h0 + 5 else koyu(goz, 0.5))
        koy(11, h0 + 8, ten[0])
        koy(8, h0 + 6, ten[0])                         # kulak
        if k.get("biyik"):
            serit(h0 + 7, 10, 12, sac[1])

    # ---- saç / örtü ----
    sac_yon = "arka" if yon == "arka" else yon
    hucre = sac_hucreleri(k, sac_yon)
    ortu = k.get("ortu", sac)
    for (x, y), tur in hucre.items():
        ramp = ortu if tur == "ortu" else sac
        c = ramp[1]
        if y - H0 in (-1, 0) and 5 <= x <= 8:
            c = ramp[2]                                # parlaklık
        elif tur == "ortu" and (x * 3 + y * 5) % 11 == 0:
            c = ramp[2]                                # örtü deseni
        elif tur == "sac" and x % 4 == 1 and y % 4 == 2 and y - H0 > 0:
            c = ramp[0]                                # saç tutamı
        koy(x, y + kay, c)

    # ---- dış hat ve iç çizgiler ----
    im = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    px = im.load()
    for (x, y), c in p.items():
        kenar = any((x + dx, y + dy) not in p for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if kenar:
            c = koyu(c, 0.42)
        elif (x, y) in ic:
            c = koyu(c, 0.6)
        px[x, y] = tuple(c) + (255,)
    return im


def sprite(k):
    sayfa = Image.new("RGBA", (64, 128), (0, 0, 0, 0))
    for satir, yon in enumerate(("on", "yan", "arka", "sol")):
        for no in range(4):
            if yon == "sol":
                f = kare(k, "yan", no).transpose(Image.FLIP_LEFT_RIGHT)
            else:
                f = kare(k, yon, no)
            sayfa.paste(f, (no * 16, satir * 32))
    return sayfa


# =================================================================== portre ===
IFADELER = ["notr", "mutlu", "uzgun", "saskin", "sevgi", "kizgin"]
AGIZ = (128, 44, 50)


def portre(k, ifade):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ten, sac, ust = k["ten"], k["sac"], k["ust"]
    stil, cocuk, yasli = k["stil"], k["tip"] == "cocuk", k["tip"] == "yasli"
    ortu = k.get("ortu", sac)
    cizgi = koyu(ten[0], 0.6)

    def cok(nokta, dolgu, kenar=None):
        d.polygon(nokta, fill=tuple(dolgu) + (255,), outline=tuple(kenar) + (255,) if kenar else None)

    def nk(x, y, c):
        if 0 <= x < 64 and 0 <= y < 64:
            im.putpixel((x, y), tuple(c) + (255,))

    def yatay(x0, x1, y, c):
        for x in range(x0, x1 + 1):
            nk(x, y, c)

    dy = 3 if cocuk else 0                             # çocukta baş biraz aşağıda

    # ---- at kuyruğu / topuz (başın arkasında) ----
    if stil == "atkuyrugu":
        cok([(44, 12), (53, 15), (58, 26), (57, 40), (52, 46), (49, 42), (51, 30), (47, 20)], sac[1], sac[0])
        d.line([(53, 20), (55, 34)], fill=sac[2] + (255,))
    if stil == "topuz":
        d.ellipse([25, 0, 39, 12], fill=sac[1] + (255,), outline=sac[0] + (255,))

    # ---- gövde ----
    omuz = 50 + dy
    govde = [(3, 64), (7, omuz + 5), (19, omuz - 1), (27, omuz - 3), (37, omuz - 3), (45, omuz - 1), (57, omuz + 5), (61, 64)]
    cok(govde, ust[1], ust[0])
    cok([(44, omuz), (56, omuz + 6), (59, 63), (49, 63)], koyu(ust[1], 0.84))
    if k.get("cizgili"):
        for y in range(omuz + 2, 64, 4):
            yatay(10, 54, y, ust[2])
    if k.get("yelek"):
        ye = k["yelek"]
        cok([(8, omuz + 5), (19, omuz - 1), (26, omuz - 2), (28, 63), (5, 63)], ye[1], ye[0])
        cok([(56, omuz + 5), (45, omuz - 1), (38, omuz - 2), (36, 63), (59, 63)], koyu(ye[1], 0.88), ye[0])
    if k.get("askili") or k.get("onluk"):
        bib = k["alt"] if k.get("askili") else k["onluk"]
        cok([(23, omuz + 5), (41, omuz + 5), (43, 63), (21, 63)], bib[1], bib[0])
        d.line([(24, omuz + 5), (25, omuz - 2)], fill=bib[0] + (255,), width=2)
        d.line([(40, omuz + 5), (39, omuz - 2)], fill=bib[0] + (255,), width=2)
        yatay(24, 40, omuz + 6, bib[2])
        if k.get("askili"):
            nk(25, omuz + 7, SARI[1])
            nk(39, omuz + 7, SARI[1])
    cok([(27, omuz - 3), (37, omuz - 3), (32, omuz + 4)], ten[1], ust[0])       # yaka
    d.line([(26, omuz - 3), (31, omuz + 4)], fill=ust[2] + (255,))
    d.line([(38, omuz - 3), (33, omuz + 4)], fill=ust[2] + (255,))

    # ---- uzun saç / küt saç / başörtüsü (omuzların üstünde, başın arkasında) ----
    if stil in ("uzun", "kut"):
        alt_y = 56 if stil == "uzun" else 44 + dy
        cok([(14, 14 + dy), (50, 14 + dy), (53, 34 + dy), (52, alt_y - 2), (45, alt_y), (41, 44 + dy),
             (23, 44 + dy), (19, alt_y), (12, alt_y - 2), (11, 34 + dy)], sac[1], sac[0])
    if stil == "basortu":
        cok([(13, 24), (15, 12), (22, 5), (32, 3), (42, 5), (49, 12), (51, 24), (51, 40), (46, 51),
             (39, 56), (25, 56), (18, 51), (13, 40)], ortu[1], ortu[0])

    # ---- boyun, kulaklar, yüz ----
    d.rectangle([27, 38 + dy, 37, omuz - 2], fill=ten[1] + (255,))
    d.rectangle([27, 40 + dy, 37, 44 + dy], fill=ten[0] + (255,))
    if stil != "basortu":
        d.ellipse([13, 25 + dy, 19, 34 + dy], fill=ten[1] + (255,), outline=cizgi + (255,))
        d.ellipse([45, 25 + dy, 51, 34 + dy], fill=ten[1] + (255,), outline=cizgi + (255,))
    if cocuk:
        yuz = [(19, 17 + dy), (45, 17 + dy), (48, 25 + dy), (47, 33 + dy), (42, 40 + dy), (36, 43 + dy),
               (28, 43 + dy), (22, 40 + dy), (17, 33 + dy), (16, 25 + dy)]
    else:
        yuz = [(19, 14), (45, 14), (47, 24), (46, 32), (42, 40), (36, 45), (28, 45), (22, 40), (18, 32), (17, 24)]
    maske = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(maske).polygon(yuz, fill=255)
    cok(yuz, ten[1], cizgi)
    mp = maske.load()
    for y in range(64):                                # sağ yanakta ve çenede gölge, alında ışık
        for x in range(64):
            if mp[x, y] and im.getpixel((x, y))[:3] == tuple(ten[1]):
                if x + 4 < 64 and not mp[x + 4, y]:
                    nk(x, y, ten[0])
                elif y + 3 < 64 and not mp[x, y + 3]:
                    nk(x, y, ten[0])
                elif x - 5 >= 0 and not mp[x - 5, y] and y < 30 + dy:
                    nk(x, y, ten[2])

    # ---- yüz hatları ----
    gy = 29 + dy
    by = 23 + dy
    ac = 3 if cocuk else 2                             # göz yüksekliği (yarı)
    for cx, yon in ((26, -1), (38, 1)):
        if ifade == "sevgi" or (ifade == "mutlu" and cocuk):
            for i, yy in enumerate((1, 0, -1, -1, -1, 0, 1)):
                nk(cx - 3 + i, gy + yy, cizgi)
                nk(cx - 3 + i, gy + yy + 1, cizgi) if i in (0, 6) else None
        else:
            ust_y = gy - ac - (1 if ifade == "saskin" else 0) + (1 if ifade in ("kizgin", "uzgun") else 0)
            alt_y = gy + ac - (1 if ifade == "kizgin" else 0)
            yatay(cx - 3, cx + 3, ust_y - 1, cizgi)                         # üst kirpik
            for y in range(ust_y, alt_y + 1):
                yatay(cx - 3, cx + 3, y, (255, 255, 255))
            nk(cx - 3, ust_y, ten[1]) if not cocuk else None
            nk(cx + 3, alt_y, ten[1])
            nk(cx - 3, alt_y, ten[1])
            for y in range(ust_y, alt_y + 1):
                yatay(cx - 1, cx + 1, y, k["goz"])
            for y in range(ust_y + 1, alt_y):
                nk(cx, y, koyu(k["goz"], 0.35))
            nk(cx - 1, ust_y, (255, 255, 255))
            yatay(cx - 2, cx + 2, alt_y + 1, ten[0])
            if k.get("kadin") and not cocuk:
                nk(cx + 4 * yon, ust_y - 1, cizgi)
                nk(cx + 4 * yon, ust_y - 2, cizgi)
        # kaşlar: dış uç -> iç uç
        dis, ic = {"notr": (0, 0), "mutlu": (-1, -1), "uzgun": (1, -2), "saskin": (-3, -3),
                   "sevgi": (-1, -1), "kizgin": (-2, 2)}[ifade]
        x_dis, x_ic = cx + 4 * yon, cx - 3 * yon
        d.line([(x_dis, by + dis), (x_ic, by + ic)], fill=sac[0] + (255,), width=2)
    # burun
    for x, y in ((33, 31), (34, 32), (34, 33), (33, 34), (32, 34), (31, 34)):
        nk(x, y + dy, ten[0])
    # ağız
    my = 39 + dy
    if ifade == "notr":
        yatay(29, 35, my, AGIZ)
        nk(28, my - 1, AGIZ)
        nk(36, my - 1, AGIZ)
    elif ifade in ("mutlu", "sevgi"):
        yatay(27, 37, my - 1, AGIZ)
        if ifade == "mutlu":
            yatay(28, 36, my, (255, 255, 255))
            yatay(29, 35, my + 1, (176, 60, 70))
            yatay(30, 34, my + 2, AGIZ)
            nk(28, my, AGIZ)
            nk(36, my, AGIZ)
        else:
            yatay(29, 35, my, AGIZ)
            nk(26, my - 2, AGIZ)
            nk(38, my - 2, AGIZ)
    elif ifade == "uzgun":
        yatay(29, 35, my - 1, AGIZ)
        nk(28, my, AGIZ)
        nk(36, my, AGIZ)
        nk(27, my + 1, AGIZ)
        nk(37, my + 1, AGIZ)
    elif ifade == "saskin":
        d.ellipse([29, my - 2, 35, my + 3], fill=(176, 60, 70, 255), outline=AGIZ + (255,))
    elif ifade == "kizgin":
        yatay(28, 36, my, AGIZ)
        yatay(29, 35, my - 1, (255, 255, 255))
        yatay(28, 36, my - 2, AGIZ)
        nk(27, my + 1, AGIZ)
        nk(37, my + 1, AGIZ)
    # yanaklar
    if ifade == "sevgi" or k.get("kadin") or cocuk:
        pembe = (252, 150, 140) if ifade == "sevgi" else (250, 176, 160)
        for cx in (22, 42):
            yatay(cx - 2, cx + 2, 34 + dy, pembe)
            yatay(cx - 1, cx + 1, 35 + dy, pembe)
            if ifade == "sevgi":
                yatay(cx - 1, cx + 1, 33 + dy, pembe)
    if yasli:                                          # kırışıklıklar
        for cx in (26, 38):
            yatay(cx - 3, cx + 2, gy + 5, ten[0])
        nk(27, 36, ten[0])
        nk(37, 36, ten[0])
    if k.get("biyik"):
        cok([(26, 36), (32, 35), (38, 36), (40, 39), (36, 37), (32, 38), (28, 37), (24, 39)], sac[1], sac[0])

    # ---- öndeki saç / örtü / şapka ----
    if stil == "basortu":
        cok([(16, 26), (17, 13), (32, 8), (47, 13), (48, 26), (45, 18), (32, 15), (19, 18)], ortu[1], ortu[0])
        cok([(14, 22), (19, 19), (19, 33), (23, 41), (29, 46), (27, 52), (19, 46), (14, 36)], ortu[1], ortu[0])
        cok([(50, 22), (45, 19), (45, 33), (41, 41), (35, 46), (37, 52), (45, 46), (50, 36)], koyu(ortu[1], 0.88), ortu[0])
        cok([(28, 46), (36, 46), (38, 53), (32, 51), (26, 53)], ortu[2], ortu[0])
        for i in range(40):                            # desen
            x, y = 14 + (i * 17) % 36, 5 + (i * 11) % 13
            if im.getpixel((x, y))[:3] == tuple(ortu[1]):
                nk(x, y, ortu[2])
    else:
        ust_y = 5 + dy
        kep = [(15, 27 + dy), (14, 17 + dy), (18, 9 + dy), (26, ust_y), (38, ust_y), (46, 9 + dy), (50, 17 + dy),
               (49, 27 + dy), (47, 22 + dy), (45, 17 + dy), (19, 17 + dy), (17, 22 + dy)]
        if stil in ("uzun", "kut"):
            kep = [(13, 34 + dy), (13, 17 + dy), (18, 9 + dy), (26, ust_y), (38, ust_y), (46, 9 + dy), (51, 17 + dy),
                   (51, 34 + dy), (47, 30 + dy), (46, 17 + dy), (18, 17 + dy), (17, 30 + dy)]
        cok(kep, sac[1], sac[0])
        perc = k.get("perc", "duz")
        if perc == "yana":
            cok([(18, 16 + dy), (46, 15 + dy), (46, 20 + dy), (37, 19 + dy), (27, 22 + dy), (18, 25 + dy)], sac[1], sac[0])
            d.line([(20, 16 + dy), (44, 15 + dy)], fill=sac[1] + (255,))
        elif perc == "orta":
            cok([(18, 16 + dy), (32, 14 + dy), (26, 20 + dy), (18, 25 + dy)], sac[1], sac[0])
            cok([(46, 16 + dy), (32, 14 + dy), (38, 20 + dy), (46, 25 + dy)], sac[1], sac[0])
        else:
            cok([(18, 16 + dy), (46, 16 + dy), (46, 22 + dy), (42, 20 + dy), (38, 22 + dy), (34, 20 + dy),
                 (30, 22 + dy), (26, 20 + dy), (22, 22 + dy), (18, 21 + dy)], sac[1], sac[0])
            d.line([(20, 16 + dy), (44, 16 + dy)], fill=sac[1] + (255,))
        d.line([(21, 11 + dy), (29, 8 + dy)], fill=sac[2] + (255,), width=2)       # parlaklık
        d.line([(35, 8 + dy), (42, 10 + dy)], fill=sac[2] + (255,))
        for x in (24, 31, 39):                         # tutamlar
            d.line([(x, 12 + dy), (x + 1, 16 + dy)], fill=sac[0] + (255,))

    # ---- dış hat ----
    kaynak = im.copy().load()
    for y in range(64):
        for x in range(64):
            if kaynak[x, y][3] and y < 63 and any(
                    0 <= x + ax < 64 and 0 <= y + ay < 64 and kaynak[x + ax, y + ay][3] == 0
                    for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), (44, 22, 34, 255))
    return im


def portre_sayfasi(k):
    sayfa = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
    for i, ifade in enumerate(IFADELER):
        sayfa.paste(portre(k, ifade), ((i % 2) * 64, (i // 2) * 64))
    return sayfa


def yaz():
    (ASSETS / "karakterler").mkdir(parents=True, exist_ok=True)
    (ASSETS / "portreler").mkdir(parents=True, exist_ok=True)
    for ad, k in KOYLULER.items():
        sprite(k).save(ASSETS / "karakterler" / f"{ad}.png")
        portre_sayfasi(k).save(ASSETS / "portreler" / f"{ad}.png")


if __name__ == "__main__":
    yaz()
    print("Yazıldı:", ", ".join(KOYLULER))
