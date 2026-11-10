#!/usr/bin/env python3
"""Çınarköy başlangıç haritasını ve karo setini üretir.

Çıktılar ([CP] Cinarkoy/assets/ içine):
  cinarkoy_tiles.png  - 16x16 karolardan oluşan özgün karo seti
  Cinarkoy.tmx        - Tiled haritası (Back / Buildings / Front katmanları)
  Tabela.tmx          - Otobüs durağına bindirilen 1x1'lik tabela yaması
Ayrıca stardew-cinarkoy/onizleme.png olarak haritanın önizlemesini çizer.

Haritayı Tiled ile elle düzenlemeye başladıktan sonra bu betiği tekrar
çalıştırma: Cinarkoy.tmx dosyasının üzerine yazar.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"
T = 16          # karo boyutu (piksel)
SUTUN = 8       # karo setindeki sütun sayısı
G, Y = 40, 30   # harita genişliği / yüksekliği (karo)

# Karo indeksleri (karo setindeki sıra)
(CIM, CICEK, TOPRAK, SU, TAS, DUVAR, CATI, KAPI,
 PENCERE, CIT, GOVDE, YAPRAK, CALI, VAGON, KUYU, CATI_UST, TABELA) = range(17)
KARO_SAYISI = 17
SATIR = (KARO_SAYISI + SUTUN - 1) // SUTUN

rng = random.Random(2941)


def benekli(taban, benekler, adet):
    """Düz renkli zemine rastgele benek atılmış 16x16 karo."""
    im = Image.new("RGBA", (T, T), taban)
    px = im.load()
    for _ in range(adet):
        px[rng.randrange(T), rng.randrange(T)] = rng.choice(benekler)
    return im


def karo_cim():
    return benekli((106, 168, 79, 255), [(92, 150, 68, 255), (124, 186, 92, 255)], 40)


def karo_cicek():
    im = karo_cim()
    d = ImageDraw.Draw(im)
    for cx, cy, renk in [(4, 5, (250, 220, 90, 255)), (11, 10, (240, 130, 170, 255))]:
        d.point([(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)], fill=renk)
        d.point((cx, cy), fill=(255, 255, 255, 255))
    return im


def karo_toprak():
    return benekli((196, 160, 106, 255), [(178, 142, 92, 255), (210, 176, 124, 255)], 35)


def karo_su():
    im = Image.new("RGBA", (T, T), (72, 140, 210, 255))
    d = ImageDraw.Draw(im)
    for y0, x0 in [(3, 2), (8, 9), (13, 4)]:
        d.line([(x0, y0), (x0 + 4, y0)], fill=(140, 195, 240, 255))
    return im


def karo_tas():
    im = Image.new("RGBA", (T, T), (150, 150, 158, 255))
    d = ImageDraw.Draw(im)
    for y0 in (0, 8):
        d.line([(0, y0), (15, y0)], fill=(112, 112, 122, 255))
    for x0, y0 in [(0, 0), (8, 0), (4, 8), (12, 8)]:
        d.line([(x0, y0), (x0, y0 + 8)], fill=(112, 112, 122, 255))
    return im


def karo_duvar():
    im = Image.new("RGBA", (T, T), (222, 196, 150, 255))
    d = ImageDraw.Draw(im)
    for y0 in (3, 7, 11, 15):
        d.line([(0, y0), (15, y0)], fill=(190, 160, 116, 255))
    return im


def karo_cati(ust=False):
    im = Image.new("RGBA", (T, T), (168, 68, 56, 255))
    d = ImageDraw.Draw(im)
    for y0 in (3, 7, 11, 15):
        d.line([(0, y0), (15, y0)], fill=(126, 44, 38, 255))
    for i, y0 in enumerate((0, 4, 8, 12)):
        for x0 in range(4 if i % 2 else 0, T, 8):
            d.line([(x0, y0), (x0, y0 + 3)], fill=(126, 44, 38, 255))
    if ust:
        d.rectangle([0, 0, 15, 2], fill=(96, 34, 30, 255))
    return im


def karo_kapi():
    im = karo_duvar()
    d = ImageDraw.Draw(im)
    d.rectangle([3, 1, 12, 15], fill=(110, 72, 40, 255), outline=(70, 44, 24, 255))
    d.point((10, 9), fill=(240, 210, 90, 255))
    return im


def karo_pencere():
    im = karo_duvar()
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, 12, 11], fill=(150, 205, 235, 255), outline=(90, 60, 36, 255))
    d.line([(8, 3), (8, 11)], fill=(90, 60, 36, 255))
    d.line([(3, 7), (12, 7)], fill=(90, 60, 36, 255))
    return im


def karo_cit():
    im = karo_cim()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 6, 15, 7], fill=(150, 104, 60, 255))
    d.rectangle([0, 11, 15, 12], fill=(150, 104, 60, 255))
    for x0 in (2, 10):
        d.rectangle([x0, 3, x0 + 2, 15], fill=(120, 80, 44, 255))
    return im


def karo_govde():
    im = karo_cim()
    d = ImageDraw.Draw(im)
    d.rectangle([5, 0, 10, 13], fill=(112, 76, 44, 255), outline=(78, 50, 28, 255))
    d.ellipse([2, 11, 13, 15], fill=(84, 138, 62, 255))
    return im


def karo_yaprak():
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 1, 15, 15], fill=(52, 122, 60, 255), outline=(34, 90, 44, 255))
    d.ellipse([3, 3, 9, 8], fill=(78, 150, 78, 255))
    return im


def karo_cali():
    im = karo_cim()
    d = ImageDraw.Draw(im)
    d.ellipse([0, 2, 15, 15], fill=(60, 128, 64, 255), outline=(38, 94, 46, 255))
    d.ellipse([3, 4, 8, 8], fill=(88, 158, 86, 255))
    return im


def karo_vagon():
    im = karo_toprak()
    d = ImageDraw.Draw(im)
    d.rectangle([1, 4, 14, 11], fill=(120, 122, 130, 255), outline=(60, 62, 70, 255))
    d.rectangle([3, 6, 12, 8], fill=(60, 44, 34, 255))
    for cx in (4, 11):
        d.ellipse([cx - 2, 11, cx + 2, 15], fill=(50, 50, 56, 255))
    return im


def karo_kuyu():
    im = karo_tas()
    d = ImageDraw.Draw(im)
    d.ellipse([1, 3, 14, 15], fill=(120, 120, 130, 255), outline=(70, 70, 80, 255))
    d.ellipse([4, 6, 11, 12], fill=(56, 110, 180, 255))
    return im


def karo_tabela():
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([7, 8, 8, 15], fill=(112, 76, 44, 255))
    d.rectangle([1, 1, 14, 8], fill=(214, 170, 104, 255), outline=(90, 58, 30, 255))
    d.polygon([(10, 3), (12, 5), (10, 7)], fill=(90, 58, 30, 255))
    d.line([(4, 5), (10, 5)], fill=(90, 58, 30, 255))
    return im


def karo_seti():
    karolar = [None] * KARO_SAYISI
    karolar[CIM] = karo_cim()
    karolar[CICEK] = karo_cicek()
    karolar[TOPRAK] = karo_toprak()
    karolar[SU] = karo_su()
    karolar[TAS] = karo_tas()
    karolar[DUVAR] = karo_duvar()
    karolar[CATI] = karo_cati()
    karolar[KAPI] = karo_kapi()
    karolar[PENCERE] = karo_pencere()
    karolar[CIT] = karo_cit()
    karolar[GOVDE] = karo_govde()
    karolar[YAPRAK] = karo_yaprak()
    karolar[CALI] = karo_cali()
    karolar[VAGON] = karo_vagon()
    karolar[KUYU] = karo_kuyu()
    karolar[CATI_UST] = karo_cati(ust=True)
    karolar[TABELA] = karo_tabela()
    sayfa = Image.new("RGBA", (SUTUN * T, SATIR * T), (0, 0, 0, 0))
    for i, k in enumerate(karolar):
        sayfa.paste(k, ((i % SUTUN) * T, (i // SUTUN) * T))
    return sayfa, karolar


# ---------------------------------------------------------------- harita ---
BOS = -1
back = [[CIM] * G for _ in range(Y)]
buildings = [[BOS] * G for _ in range(Y)]
front = [[BOS] * G for _ in range(Y)]

# Vagonun durduğu karo ve oyuncunun köye vardığı karo (content.json ile aynı olmalı)
VAGON_KARO = (4, 13)
VARIS_KARO = (4, 14)
# Otobüs durağına dönüş tabelası (content.json ile aynı olmalı)
TABELA_KARO = (6, 13)


def dikdortgen(katman, x0, y0, x1, y1, karo):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            katman[y][x] = karo


def ev(x0, y0, genislik=5):
    """Üst sol köşesi (x0, y0) olan ev: 2 sıra çatı + 2 sıra duvar."""
    x1 = x0 + genislik - 1
    dikdortgen(buildings, x0, y0, x1, y0, CATI_UST)
    dikdortgen(buildings, x0, y0 + 1, x1, y0 + 1, CATI)
    dikdortgen(buildings, x0, y0 + 2, x1, y0 + 3, DUVAR)
    buildings[y0 + 2][x0 + 1] = PENCERE
    buildings[y0 + 2][x1 - 1] = PENCERE
    kapi_x = x0 + genislik // 2
    buildings[y0 + 3][kapi_x] = KAPI
    return kapi_x, y0 + 4      # kapının önündeki karo


def agac(x, y):
    buildings[y][x] = GOVDE
    front[y - 1][x] = YAPRAK


# Çiçekler
for _ in range(90):
    back[rng.randrange(1, Y - 1)][rng.randrange(1, G - 1)] = CICEK

# Yollar: doğu-batı ana yol, kuzey-güney ara yol, ortada taş meydan
dikdortgen(back, 2, 14, G - 3, 15, TOPRAK)
dikdortgen(back, 19, 3, 20, Y - 4, TOPRAK)
dikdortgen(back, 15, 11, 24, 18, TAS)
buildings[13][17] = KUYU

# Gölet
dikdortgen(back, 29, 20, 35, 25, SU)
for x, y in [(29, 20), (35, 20), (29, 25), (35, 25)]:
    back[y][x] = CIM

# Evler ve kapı önü patikaları (patika en yakın yola kadar iner/çıkar)
for x0, y0 in [(5, 6), (11, 6), (25, 6), (32, 6)]:
    kx, ky = ev(x0, y0)
    dikdortgen(back, kx, ky, kx, 13, TOPRAK)
for x0, y0 in [(6, 19), (22, 21)]:
    kx, ky = ev(x0, y0)
    dikdortgen(back, kx, 16, kx, y0 - 1, TOPRAK)
    # Güneydeki evlerin kapısı güneye bakıyor; yola çıkmak için evin yanından dolan
    dikdortgen(back, kx, ky, x0 + 5, ky, TOPRAK)
    dikdortgen(back, x0 + 5, y0 - 1, x0 + 5, ky, TOPRAK)
    dikdortgen(back, kx, y0 - 1, x0 + 5, y0 - 1, TOPRAK)

# Çitle çevrili bahçe (güney kenarında giriş boşluğu var)
for x in range(12, 18):
    buildings[20][x] = CIT
    if x not in (14, 15):
        buildings[25][x] = CIT
for y in range(20, 26):
    buildings[y][12] = CIT
    buildings[y][17] = CIT

# Vagon durağı
buildings[VAGON_KARO[1]][VAGON_KARO[0]] = VAGON

buildings[TABELA_KARO[1]][TABELA_KARO[0]] = TABELA

# Sınır: haritanın kenarı çalıyla kapalı
for x in range(G):
    buildings[0][x] = CALI
    buildings[Y - 1][x] = CALI
for y in range(Y):
    buildings[y][0] = CALI
    buildings[y][G - 1] = CALI

# Ağaçlar: yalnızca boş çimenlere
adaylar = [(x, y) for y in range(3, Y - 2) for x in range(2, G - 2)]
rng.shuffle(adaylar)
dikilen = 0
for x, y in adaylar:
    if dikilen >= 26:
        break
    cevre_bos = all(
        buildings[yy][xx] == BOS and front[yy][xx] == BOS and back[yy][xx] in (CIM, CICEK)
        for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
    )
    if cevre_bos and (x, y) != VARIS_KARO:
        agac(x, y)
        dikilen += 1

assert buildings[VARIS_KARO[1]][VARIS_KARO[0]] == BOS, "Varış karosu dolu!"


# ---------------------------------------------------------------- çıktı ----
def csv(katman):
    return ",\n".join(",".join(str(k + 1) for k in satir) for satir in katman)


def ozellik(karo, **ozellikler):
    ic = "".join(f'\n    <property name="{ad}" value="{deger}"/>' for ad, deger in ozellikler.items())
    return f'  <tile id="{karo}">\n   <properties>{ic}\n   </properties>\n  </tile>\n'


def tileset(karo_ozellikleri=""):
    return (
        f' <tileset firstgid="1" name="cinarkoy_tiles" tilewidth="{T}" tileheight="{T}" '
        f'tilecount="{SATIR * SUTUN}" columns="{SUTUN}">\n'
        f'  <image source="cinarkoy_tiles.png" width="{SUTUN * T}" height="{SATIR * T}"/>\n'
        f'{karo_ozellikleri}'
        ' </tileset>\n'
    )


def tabela_yamasi_yaz():
    """Vanilla haritaya bindirilen 1x1'lik yama: yalnızca tabela karosu."""
    tmx = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" '
        f'width="1" height="1" tilewidth="{T}" tileheight="{T}" infinite="0" '
        'nextlayerid="2" nextobjectid="1">\n'
        f'{tileset()}'
        ' <layer id="1" name="Buildings" width="1" height="1">\n'
        f'  <data encoding="csv">\n{TABELA + 1}\n</data>\n </layer>\n'
        '</map>\n'
    )
    (ASSETS / "Tabela.tmx").write_text(tmx, encoding="utf-8")


def tmx_yaz():
    karo_ozellikleri = (
        ozellik(CIM, Type="Grass")
        + ozellik(CICEK, Type="Grass")
        + ozellik(TOPRAK, Type="Dirt")
        + ozellik(SU, Water="T", Passable="F")
        + ozellik(TAS, Type="Stone")
    )
    katmanlar = "".join(
        f' <layer id="{i}" name="{ad}" width="{G}" height="{Y}">\n'
        f'  <data encoding="csv">\n{csv(veri)}\n</data>\n </layer>\n'
        for i, (ad, veri) in enumerate([("Back", back), ("Buildings", buildings), ("Front", front)], 1)
    )
    tmx = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" '
        f'width="{G}" height="{Y}" tilewidth="{T}" tileheight="{T}" infinite="0" '
        f'nextlayerid="4" nextobjectid="1">\n'
        ' <properties>\n'
        '  <property name="Outdoors" value="T"/>\n'
        ' </properties>\n'
        f'{tileset(karo_ozellikleri)}'
        f'{katmanlar}'
        '</map>\n'
    )
    (ASSETS / "Cinarkoy.tmx").write_text(tmx, encoding="utf-8")


def onizleme(karolar):
    im = Image.new("RGBA", (G * T, Y * T))
    for katman in (back, buildings, front):
        for y in range(Y):
            for x in range(G):
                if katman[y][x] != BOS:
                    im.alpha_composite(karolar[katman[y][x]], (x * T, y * T))
    im.resize((G * T * 2, Y * T * 2), Image.NEAREST).save(KOK / "onizleme.png")


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    sayfa, karolar = karo_seti()
    sayfa.save(ASSETS / "cinarkoy_tiles.png")
    tmx_yaz()
    tabela_yamasi_yaz()
    onizleme(karolar)
    print(f"Tamam: {G}x{Y} harita, {dikilen} ağaç")
