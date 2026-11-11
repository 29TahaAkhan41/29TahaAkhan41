#!/usr/bin/env python3
"""Çınarköy haritasını üretir.

Kullanım:
    python3 tools/harita_uret.py "<oyun klasörü>/Content (unpacked)/Maps"

Binalar tamamen özgündür: tools/ev_ciz.py onları sıfırdan çizer. Zemin (çimen,
toprak yol), ağaçlar, vagon ve tabela için oyunun kendi karoları kullanılır;
bunların düzeni oyunun açılmış (StardewXnbHack) Town.tmx / BusStop.tmx
haritalarından okunur. Oyunun görselleri moda KOPYALANMAZ; harita o karo
setlerine yalnızca adlarıyla başvurur.

Çıktılar:
    [CP] Cinarkoy/assets/Cinarkoy.tmx                   köy haritası
    [CP] Cinarkoy/assets/Tabela.tmx                     otobüs durağı tabela yaması
    [CP] Cinarkoy/assets/<mevsim>_cinarkoy_evler.png    özgün bina karoları
    onizleme.png                                         haritanın önizlemesi

Haritayı Tiled ile elle düzenlemeye başladıktan sonra bu betiği tekrar
çalıştırma: Cinarkoy.tmx dosyasının üzerine yazar.
"""
import copy
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

import ev_ciz

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"
G, Y = 60, 50                     # harita boyutu (karo)
rng = random.Random(2941)

# content.json ile aynı olmalı
VAGON = (6, 18)                   # ray parçasının üst karosu
TABELA = (10, 21)                 # tabela direği (Buildings)
VARIS_VAGON = (6, 22)
VARIS_TABELA = (10, 22)


# ------------------------------------------------------------ TMX okuma ---
class Harita:
    def __init__(self, yol):
        self.kok = ET.parse(yol).getroot()
        self.g = int(self.kok.get("width"))
        self.y = int(self.kok.get("height"))
        self.setler = {ts.find("image").get("source"): ts for ts in self.kok.findall("tileset")}
        self.katman = {}
        for l in self.kok.findall("layer"):
            v = [int(x) for x in l.find("data").text.replace("\n", "").split(",") if x.strip()]
            self.katman[l.get("name")] = [v[i * self.g:(i + 1) * self.g] for i in range(self.y)]

    def ilk(self, kaynak):
        return int(self.setler[kaynak].get("firstgid"))


if len(sys.argv) != 2:
    sys.exit(__doc__)
MAPS = Path(sys.argv[1])
town = Harita(MAPS / "Town.tmx")
bus = Harita(MAPS / "BusStop.tmx")

# Town.tmx'teki karo seti sırası ve numaraları aynen kullanılır
KATMANLAR = ["Back", "Back2", "Back3", "Buildings", "Buildings2", "Paths", "Front", "AlwaysFront"]
SETLER = ["spring_outdoorsTileSheet", "paths", "spring_town", "spring_Shadows"]
assert town.ilk("spring_outdoorsTileSheet") == 1 and bus.ilk("spring_outdoorsTileSheet") == 1

harita = {ad: [[0] * G for _ in range(Y)] for ad in KATMANLAR}


def dolu(x, y, katmanlar=("Buildings", "Buildings2", "Front", "AlwaysFront")):
    return any(harita[k][y][x] for k in katmanlar)


# ---------------------------------------------------------------- zemin ---
# Köşe tabanlı döşeme: her karonun 4 köşesi (sol üst, sağ üst, sol alt, sağ alt)
# toprak (d) ya da çimen (g). Karo numaraları spring_outdoorsTileSheet içinden.
KENAR = {
    "dddg": 179, "ddgd": 253, "ddgg": 252, "dgdd": 178, "dgdg": 229, "dggg": 254,
    "gddd": 203, "gdgd": 226, "gdgg": 251, "ggdd": 202, "ggdg": 204, "gggd": 201,
}
CIMEN = [176] * 46 + [327, 327, 353, 152, 153]
TOPRAK = [228] * 40 + [227] * 6 + [561, 590, 208, 154]

toprak = [[False] * (G + 1) for _ in range(Y + 1)]     # köşe ızgarası


def yol(x0, y0, x1, y1):
    """(x0,y0)-(x1,y1) karolarını (dahil) toprak yap."""
    for y in range(y0, y1 + 2):
        for x in range(x0, x1 + 2):
            toprak[y][x] = True


def zemini_dose():
    # Çapraz köşe karosu yok: öyle hücreleri tamamen toprak yap
    degisti = True
    while degisti:
        degisti = False
        for y in range(Y):
            for x in range(G):
                k = (toprak[y][x], toprak[y][x + 1], toprak[y + 1][x], toprak[y + 1][x + 1])
                if k in ((True, False, False, True), (False, True, True, False)):
                    toprak[y][x] = toprak[y][x + 1] = toprak[y + 1][x] = toprak[y + 1][x + 1] = True
                    degisti = True
    for y in range(Y):
        for x in range(G):
            k = "".join("d" if t else "g" for t in
                        (toprak[y][x], toprak[y][x + 1], toprak[y + 1][x], toprak[y + 1][x + 1]))
            harita["Back"][y][x] = (rng.choice(TOPRAK) if k == "dddd"
                                    else rng.choice(CIMEN) if k == "gggg" else KENAR[k])


# ---------------------------------------------------------------- damga ---
def damga(kaynak, kx0, ky0, kx1, ky1, hx, hy, filtre):
    """Kaynak haritanın (kx0,ky0)-(kx1,ky1) bölgesini (hx,hy)'ye kopyalar.
    filtre(katman, gid) True dönen karolar alınır."""
    for ad in KATMANLAR:
        if ad not in kaynak.katman:
            continue
        for y in range(ky0, ky1 + 1):
            for x in range(kx0, kx1 + 1):
                gid = kaynak.katman[ad][y][x]
                if gid and filtre(ad, gid):
                    harita[ad][hy + y - ky0][hx + x - kx0] = gid


# --------------------------------------------------------- özgün binalar ---
EV_SAYFA, EV_YER = ev_ciz.yaz()           # karo setlerini yazar, yerleşim bilgisini verir
EV0 = 6000                                # özgün karo setinin ilk numarası
EV_SUTUN = ev_ciz.SAYFA_SUTUN


def bina(ad, hx, hy):
    """Binayı sol üst köşesi (hx,hy) olacak şekilde yerleştirir. Üstteki sıralar
    Front (arkasından yürünür), gövde Buildings (engel) katmanına gider.
    Dönen: (kapı sütunları, binanın hemen altındaki sıra)."""
    kx, ky, gk, yk, on, kapi = EV_YER[ad]
    for y in range(yk):
        for x in range(gk):
            sx, sy = (kx + x) * 16, (ky + y) * 16
            if EV_SAYFA.crop((sx, sy, sx + 16, sy + 16)).getbbox():
                harita["Front" if y < on else "Buildings"][hy + y][hx + x] = EV0 + (ky + y) * EV_SUTUN + kx + x
    return [hx + k for k in kapi], hy + yk


# --------------------------------------------------------------- ağaçlar ---
def agac_ogren(govde, sutun0, genislik, tac_satir, govdeler):
    """Town.tmx'te bu ağacın en eksiksiz örneğini bulup katman düzenini öğrenir.
    Dönen: [(katman, dx, dy, gid)], (0,0) = kök karosu."""
    gidler = {r * 25 + sutun0 + c + 1 for r in range(tac_satir) for c in range(genislik)} | set(govdeler)
    yari = genislik // 2
    en_iyi = []
    for y in range(8, town.y):
        for x in range(yari, town.g - yari):
            if town.katman["Buildings"][y][x] != govde:
                continue
            bulunan = []
            for ad in ("Buildings", "Buildings2", "Front", "AlwaysFront"):
                for dy in range(-(tac_satir + 2), 1):
                    for dx in range(-yari, yari + 1):
                        gid = town.katman[ad][y + dy][x + dx]
                        if gid in gidler:
                            bulunan.append((ad, dx, dy, gid))
            if len(bulunan) > len(en_iyi):
                en_iyi = bulunan
    assert en_iyi, f"ağaç bulunamadı: {govde}"
    return en_iyi


MESE = agac_ogren(127, 0, 3, 4, [102, 127])
MESE2 = agac_ogren(130, 3, 3, 4, [105, 130])
PEMBE = agac_ogren(144, 17, 5, 4, [119, 120, 144, 145, 169, 170])


def agac(tur, x, y, zorla=False):
    """Kökü (x,y)'de olan ağaç diker; yer doluysa dikmez."""
    hucreler = [(ad, x + dx, y + dy, gid) for ad, dx, dy, gid in tur]
    if any(not (0 <= cx < G and 0 <= cy < Y) for _, cx, cy, _ in hucreler):
        return False
    if not zorla:
        if any(dolu(cx, cy) for _, cx, cy, _ in hucreler):
            return False
        if any(harita["Back"][cy][cx] not in CIMEN for ad, cx, cy, _ in hucreler if ad.startswith("Buildings")):
            return False
    for ad, cx, cy, gid in hucreler:
        harita[ad][cy][cx] = gid
    return True


# ------------------------------------------------------------- yerleşim ---
ANA_YOL = (22, 23)                    # doğu-batı ana yolun sıraları
yol(4, ANA_YOL[0], 55, ANA_YOL[1])
yol(25, 18, 37, 21)                   # meydan
# Güney sırasına inen iki patika ve onları birleştiren alt yol
yol(27, 24, 28, 40)
yol(38, 24, 39, 40)
yol(10, 39, 46, 40)

KUZEY = [("iki_katli", 13, 8), ("dukkan", 40, 12)]                  # kapılar ana yola bakar
GUNEY = [("tas_kulube", 7, 31), ("ahsap_ev", 18, 29), ("ahir", 30, 29), ("siva_kulube", 42, 31)]
KAPILAR = []
for ad, hx, hy in KUZEY + GUNEY:
    kx, ky, gk, yk, on, kapi = EV_YER[ad]
    alt = hy + yk
    yol(hx + kapi[0], alt, hx + kapi[-1], ANA_YOL[0] - 1 if (ad, hx, hy) in KUZEY else 38)
    KAPILAR.append((ad, hx + kapi[0], alt - 1))

zemini_dose()
for ad, hx, hy in KUZEY + GUNEY:
    bina(ad, hx, hy)
bina("kuyu", 30, 16)

# Vagon: Town'daki ray + vagon + kol
damga(town, 105, 77, 105, 80, VAGON[0], VAGON[1], lambda ad, gid: gid not in CIMEN and ad != "Paths")
damga(town, 106, 79, 107, 79, VAGON[0] + 1, VAGON[1] + 2, lambda ad, gid: ad not in ("Back", "Paths"))
VAGON_TIK = [(VAGON[0], y) for y in range(VAGON[1], VAGON[1] + 4) if harita["Buildings"][y][VAGON[0]]]

# Tabela: BusStop'taki yön tabelası
TABELA_UST = bus.katman["Front"][21][21]
TABELA_ALT = bus.katman["Buildings"][22][21]
harita["Front"][TABELA[1] - 1][TABELA[0]] = TABELA_UST
harita["Buildings"][TABELA[1]][TABELA[0]] = TABELA_ALT

# Meydanın iki yanında kiraz ağaçları
agac(PEMBE, 24, 15)
agac(PEMBE, 37, 15)

# Kenar: haritayı çevreleyen ağaç şeridi (taçlar üst üste binmeden)
for x in range(1, G - 1, 3):
    agac(rng.choice((MESE, MESE2)), x, 5)
    agac(rng.choice((MESE, MESE2)), x, Y - 1)
for y in range(9, Y - 4, 4):
    agac(rng.choice((MESE, MESE2)), 1, y)
    agac(rng.choice((MESE, MESE2)), G - 2, y)

# İçeride serpiştirilmiş ağaçlar
dikilen, deneme = 0, 0
while dikilen < 14 and deneme < 4000:
    deneme += 1
    x, y = rng.randrange(5, G - 5), rng.randrange(12, Y - 7)
    cevre_bos = all(not dolu(cx, cy) and harita["Back"][cy][cx] in CIMEN
                    for cy in range(y - 6, y + 2) for cx in range(x - 2, x + 3))
    if cevre_bos and agac(rng.choice((MESE, MESE2)), x, y):
        dikilen += 1

for vx, vy in (VARIS_VAGON, VARIS_TABELA):
    assert not dolu(vx, vy, ("Buildings", "Buildings2")), "Varış karosu dolu!"


# ---------------------------------------------------------------- çıktı ---
def set_xml(kaynak_harita, kaynak):
    ts = copy.deepcopy(kaynak_harita.setler[kaynak])
    ts.find("image").set("source", kaynak + ".png")
    ts.tail = "\n "
    return ET.tostring(ts, encoding="unicode").rstrip()


def katman_xml(i, ad, veri, g, y):
    csv = ",\n".join(",".join(map(str, satir)) for satir in veri)
    return f' <layer id="{i}" name="{ad}" width="{g}" height="{y}">\n  <data encoding="csv">\n{csv}\n</data>\n </layer>\n'


def tmx(g, y, setler, katmanlar, ozellikler=""):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<map version="1.4" tiledversion="1.4.2" orientation="orthogonal" renderorder="right-down" '
            f'width="{g}" height="{y}" tilewidth="16" tileheight="16" infinite="0" '
            f'nextlayerid="{len(katmanlar) + 1}" nextobjectid="1">\n'
            + ozellikler
            + "".join(" " + s + "\n" for s in setler)
            + "".join(katman_xml(i, ad, veri, g, y) for i, (ad, veri) in enumerate(katmanlar, 1))
            + "</map>\n")


EV_SET = (f'<tileset firstgid="{EV0}" name="cinarkoy_evler" tilewidth="16" tileheight="16" '
          f'tilecount="{EV_SAYFA.width // 16 * (EV_SAYFA.height // 16)}" columns="{EV_SUTUN}">\n'
          f'  <image source="spring_cinarkoy_evler.png" width="{EV_SAYFA.width}" height="{EV_SAYFA.height}"/>\n'
          ' </tileset>')


def kullanilan_setler():
    """Yalnızca haritada gerçekten kullanılan oyun karo setleri."""
    gidler = {g for ad in KATMANLAR for satir in harita[ad] for g in satir if 0 < g < EV0}
    secilen = []
    for s in SETLER:
        ilk = town.ilk(s)
        if any(ilk <= g < ilk + int(town.setler[s].get("tilecount")) for g in gidler):
            secilen.append(s)
    return secilen


def yaz():
    ASSETS.mkdir(parents=True, exist_ok=True)
    koy = tmx(G, Y, [set_xml(town, s) for s in kullanilan_setler()] + [EV_SET], [(ad, harita[ad]) for ad in KATMANLAR],
              ' <properties>\n  <property name="Outdoors" type="string" value="T"/>\n </properties>\n')
    (ASSETS / "Cinarkoy.tmx").write_text(koy, encoding="utf-8")
    # Otobüs durağı yaması: 1x2, üstte tabela levhası (Front), altta direk (Buildings)
    yama = tmx(1, 2, [set_xml(bus, "spring_outdoorsTileSheet")],
               [("Buildings", [[0], [TABELA_ALT]]), ("Front", [[TABELA_UST], [0]])])
    (ASSETS / "Tabela.tmx").write_text(yama, encoding="utf-8")


def onizleme():
    sayfalar = []
    for s in kullanilan_setler():
        ts = town.setler[s]
        sayfalar.append((int(ts.get("firstgid")), int(ts.get("columns")),
                         Image.open(MAPS / f"{s}.png").convert("RGBA")))
    sayfalar.append((EV0, EV_SUTUN, EV_SAYFA))
    im = Image.new("RGBA", (G * 16, Y * 16), (0, 0, 0, 255))
    for ad in KATMANLAR:
        if ad == "Paths":
            continue
        for y in range(Y):
            for x in range(G):
                gid = harita[ad][y][x]
                if not gid:
                    continue
                ilk, sutun, sayfa = [s for s in sayfalar if s[0] <= gid][-1]
                i = gid - ilk
                kx, ky = (i % sutun) * 16, (i // sutun) * 16
                im.alpha_composite(sayfa.crop((kx, ky, kx + 16, ky + 16)), (x * 16, y * 16))
    im.resize((G * 32, Y * 32), Image.NEAREST).save(KOK / "onizleme.png")


if __name__ == "__main__":
    yaz()
    onizleme()
    print(f"Tamam: {G}x{Y} harita, {dikilen} iç ağaç")
    print("Vagon tıklama karoları (Buildings):", VAGON_TIK)
    print("Oyun karo setleri:", kullanilan_setler())
    print("Kapılar (bina, x, y):", KAPILAR)
